"""
AI Service - Handles LLM integration via Bytez SDK.
Manages context windows, response generation, and fallback strategies.
Uses bytez package to access models like openai/gpt-4o and openai/gpt-4o-mini.
"""
import logging
import time
from flask import current_app
from ..extensions import db
from ..models.conversation import Conversation
from ..models.message import Message
from ..utils.errors import AIServiceError

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with AI models via the Bytez SDK."""

    DEFAULT_SYSTEM_PROMPT = (
        "You are a helpful, intelligent AI assistant. You provide clear, accurate, "
        "and concise responses. You are part of an automation platform and can help "
        "users with their questions, tasks, and workflows."
    )

    def __init__(self):
        self._sdk = None
        self._primary_model = None
        self._fallback_model = None

    def _get_sdk(self):
        """Lazy-load the Bytez SDK."""
        if self._sdk is None:
            api_key = current_app.config.get('BYTEZ_API_KEY', '')
            if not api_key:
                logger.warning("No BYTEZ_API_KEY configured - using mock responses")
                return None
            try:
                from bytez import Bytez
                self._sdk = Bytez(api_key)
            except ImportError:
                logger.warning("bytez package not installed - using mock responses")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Bytez SDK: {e}")
                return None
        return self._sdk

    def _get_model(self, model_name):
        """Get a Bytez model instance by name."""
        sdk = self._get_sdk()
        if not sdk:
            return None
        try:
            return sdk.model(model_name)
        except Exception as e:
            logger.error(f"Failed to load model '{model_name}': {e}")
            return None

    def build_context(self, conversation_id, new_message_content):
        """Build the message context for the AI model."""
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            raise AIServiceError('Conversation not found')

        window_size = current_app.config.get('CONTEXT_WINDOW_SIZE', 20)
        messages = []

        # System prompt
        system_prompt = conversation.system_prompt or self.DEFAULT_SYSTEM_PROMPT
        messages.append({
            'role': 'system',
            'content': system_prompt
        })

        # Add conversation summary if available (for long conversations)
        if conversation.summary:
            messages.append({
                'role': 'system',
                'content': f"Previous conversation summary: {conversation.summary}"
            })

        # Fetch recent messages for context window
        recent_messages = (
            Message.query
            .filter_by(conversation_id=conversation_id)
            .order_by(Message.created_at.desc())
            .limit(window_size)
            .all()
        )

        # Reverse to chronological order
        for msg in reversed(recent_messages):
            messages.append({
                'role': msg.role,
                'content': msg.content
            })

        # Add the new user message
        messages.append({
            'role': 'user',
            'content': new_message_content
        })

        return messages

    def generate_response(self, conversation_id, user_message_content):
        """Generate a complete (non-streaming) AI response using Bytez SDK."""
        context = self.build_context(conversation_id, user_message_content)
        model_name = current_app.config.get('OPENAI_MODEL', 'openai/gpt-4o')
        fallback_model_name = current_app.config.get('OPENAI_FALLBACK_MODEL', 'openai/gpt-4o-mini')

        sdk = self._get_sdk()
        if not sdk:
            # Mock response for development without API key
            return self._mock_response(user_message_content)

        # Try primary model
        try:
            model = sdk.model(model_name)
            results = model.run(context)

            if results.error:
                raise Exception(f"Bytez API error: {results.error}")

            content = self._extract_content(results.output)
            return {
                'content': content,
                'tokens_used': 0,  # Bytez doesn't return token counts in the same way
                'model': model_name,
            }

        except Exception as e:
            logger.warning(f"Primary model '{model_name}' failed: {e}, trying fallback")

            # Try fallback model
            try:
                fallback_model = sdk.model(fallback_model_name)
                results = fallback_model.run(context)

                if results.error:
                    raise Exception(f"Bytez API error: {results.error}")

                content = self._extract_content(results.output)
                return {
                    'content': content,
                    'tokens_used': 0,
                    'model': fallback_model_name,
                }

            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {fallback_error}")
                raise AIServiceError(f'AI service unavailable: {str(fallback_error)}')

    def generate_streaming_response(self, conversation_id, user_message_content):
        """Generate a streaming-like AI response (yields chunks).
        Note: Bytez SDK may not natively support streaming, so we simulate
        it by splitting the complete response into word-level chunks.
        """
        context = self.build_context(conversation_id, user_message_content)
        model_name = current_app.config.get('OPENAI_MODEL', 'openai/gpt-4o')

        sdk = self._get_sdk()
        if not sdk:
            yield from self._mock_streaming_response(user_message_content)
            return

        try:
            model = sdk.model(model_name)
            results = model.run(context)

            if results.error:
                raise Exception(f"Bytez API error: {results.error}")

            content = self._extract_content(results.output)

            # Simulate streaming by yielding word-by-word
            words = content.split(' ')
            for i, word in enumerate(words):
                yield {
                    'content': word + (' ' if i < len(words) - 1 else ''),
                    'model': model_name,
                }
                time.sleep(0.03)

        except Exception as e:
            logger.error(f"Streaming response failed: {e}")
            raise AIServiceError(f'AI streaming failed: {str(e)}')

    def summarize_conversation(self, conversation_id):
        """Generate a summary of a conversation for context compression."""
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            raise AIServiceError('Conversation not found')

        messages = (
            Message.query
            .filter_by(conversation_id=conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )

        if len(messages) < 10:
            return None  # Too short to summarize

        conversation_text = "\n".join(
            f"{msg.role}: {msg.content}" for msg in messages
        )

        summary_prompt = [
            {
                'role': 'system',
                'content': 'Summarize the following conversation in 2-3 sentences, '
                           'capturing the key topics and any decisions made.'
            },
            {
                'role': 'user',
                'content': conversation_text
            }
        ]

        sdk = self._get_sdk()
        if not sdk:
            return "Conversation summary not available (no API key configured)."

        try:
            fallback_model_name = current_app.config.get('OPENAI_FALLBACK_MODEL', 'openai/gpt-4o-mini')
            model = sdk.model(fallback_model_name)
            results = model.run(summary_prompt)

            if results.error:
                raise Exception(f"Bytez API error: {results.error}")

            summary = self._extract_content(results.output)
            conversation.summary = summary
            db.session.commit()
            return summary
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None

    def generate_conversation_title(self, first_message):
        """Generate a title for a new conversation based on the first message."""
        sdk = self._get_sdk()
        if not sdk:
            # Simple fallback: use first 50 chars of message
            return first_message[:50] + ('...' if len(first_message) > 50 else '')

        try:
            fallback_model_name = current_app.config.get('OPENAI_FALLBACK_MODEL', 'openai/gpt-4o-mini')
            model = sdk.model(fallback_model_name)
            results = model.run([
                {
                    'role': 'system',
                    'content': 'Generate a short title (max 6 words) for a conversation '
                               'that starts with the following message. Return only the title, no quotes.'
                },
                {'role': 'user', 'content': first_message}
            ])

            if results.error:
                raise Exception(f"Bytez API error: {results.error}")

            return self._extract_content(results.output).strip()
        except Exception:
            return first_message[:50] + ('...' if len(first_message) > 50 else '')

    def _extract_content(self, output):
        """Extract text content from Bytez SDK output.
        The output format may vary, so we handle different structures.
        """
        if isinstance(output, str):
            return output

        # Handle dict response (e.g., {"choices": [{"message": {"content": "..."}}]})
        if isinstance(output, dict):
            # OpenAI-style response via Bytez
            choices = output.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                if isinstance(message, dict):
                    return message.get('content', str(output))
                return str(message)
            # Direct content field
            if 'content' in output:
                return output['content']
            # Fallback to string representation
            return str(output)

        # Handle list response
        if isinstance(output, list) and len(output) > 0:
            first = output[0]
            if isinstance(first, dict):
                return first.get('content', first.get('text', str(first)))
            return str(first)

        return str(output)

    def _mock_response(self, user_message):
        """Generate a mock response for development without an API key."""
        responses = {
            'hello': "Hello! I'm your AI assistant. How can I help you today?",
            'help': "I can help you with:\n• Answering questions\n• Creating automation workflows\n• Analyzing data\n• General conversation\n\nJust type your question!",
        }

        # Check for keyword matches
        lower_msg = user_message.lower().strip()
        for keyword, response in responses.items():
            if keyword in lower_msg:
                return {
                    'content': response,
                    'tokens_used': 0,
                    'model': 'mock',
                }

        return {
            'content': f"I received your message: \"{user_message}\"\n\nI'm running in development mode without a Bytez API key. To enable AI-powered responses, set the BYTEZ_API_KEY in your .env file.",
            'tokens_used': 0,
            'model': 'mock',
        }

    def _mock_streaming_response(self, user_message):
        """Generate a mock streaming response."""
        response = self._mock_response(user_message)
        words = response['content'].split(' ')
        for i, word in enumerate(words):
            yield {
                'content': word + (' ' if i < len(words) - 1 else ''),
                'model': 'mock',
            }
            time.sleep(0.05)  # Simulate streaming delay


# Singleton instance
ai_service = AIService()
