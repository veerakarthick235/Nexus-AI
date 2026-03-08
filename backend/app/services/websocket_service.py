"""
WebSocket service for real-time chat communication.
"""
import logging
from flask import request
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import decode_token

logger = logging.getLogger(__name__)

# Track connected users
connected_users = {}


def register_socket_events(socketio):
    """Register all WebSocket event handlers."""

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        token = request.args.get('token')
        if token:
            try:
                decoded = decode_token(token)
                user_id = decoded.get('sub')
                connected_users[request.sid] = user_id
                logger.info(f"WebSocket connected: user={user_id}, sid={request.sid}")
                emit('connected', {'status': 'ok', 'user_id': user_id})
            except Exception as e:
                logger.warning(f"WebSocket auth failed: {e}")
                emit('error', {'message': 'Authentication failed'})
                return False
        else:
            logger.warning("WebSocket connection without token")
            emit('error', {'message': 'Token required'})
            return False

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        user_id = connected_users.pop(request.sid, None)
        logger.info(f"WebSocket disconnected: user={user_id}, sid={request.sid}")

    @socketio.on('join_conversation')
    def handle_join_conversation(data):
        """Join a conversation room for real-time updates."""
        conversation_id = data.get('conversation_id')
        if conversation_id:
            room = f"conversation_{conversation_id}"
            join_room(room)
            logger.info(f"User joined room: {room}")
            emit('joined', {'conversation_id': conversation_id, 'room': room})

    @socketio.on('leave_conversation')
    def handle_leave_conversation(data):
        """Leave a conversation room."""
        conversation_id = data.get('conversation_id')
        if conversation_id:
            room = f"conversation_{conversation_id}"
            leave_room(room)
            logger.info(f"User left room: {room}")

    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle a chat message sent via WebSocket."""
        user_id = connected_users.get(request.sid)
        if not user_id:
            emit('error', {'message': 'Not authenticated'})
            return

        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()

        if not conversation_id or not content:
            emit('error', {'message': 'conversation_id and content are required'})
            return

        room = f"conversation_{conversation_id}"

        try:
            # Import here to avoid circular imports
            from ..extensions import db
            from ..models.message import Message
            from ..models.conversation import Conversation
            from ..services.ai_service import ai_service

            # Store user message
            user_message = Message(
                conversation_id=conversation_id,
                role='user',
                content=content,
            )
            db.session.add(user_message)

            # Update conversation
            conversation = Conversation.query.get(conversation_id)
            if conversation:
                conversation.message_count = (conversation.message_count or 0) + 1

            db.session.commit()

            # Emit the user message to the room
            emit('new_message', user_message.to_dict(), room=room)

            # Show typing indicator
            emit('typing_start', {'conversation_id': conversation_id}, room=room)

            # Generate AI response (streaming)
            full_response = ''
            model_used = 'mock'

            for chunk in ai_service.generate_streaming_response(conversation_id, content):
                chunk_content = chunk.get('content', '')
                model_used = chunk.get('model', model_used)
                full_response += chunk_content
                emit('message_chunk', {
                    'conversation_id': conversation_id,
                    'content': chunk_content,
                    'model': model_used,
                }, room=room)

            # Store assistant message
            assistant_message = Message(
                conversation_id=conversation_id,
                role='assistant',
                content=full_response,
                model=model_used,
            )
            db.session.add(assistant_message)

            if conversation:
                conversation.message_count = (conversation.message_count or 0) + 1

            db.session.commit()

            # Emit typing stop and complete message
            emit('typing_stop', {'conversation_id': conversation_id}, room=room)
            emit('message_complete', assistant_message.to_dict(), room=room)

        except Exception as e:
            logger.error(f"WebSocket message handling failed: {e}")
            emit('typing_stop', {'conversation_id': conversation_id}, room=room)
            emit('error', {'message': f'Failed to process message: {str(e)}'})

    @socketio.on('typing')
    def handle_typing(data):
        """Broadcast typing indicator to conversation room."""
        conversation_id = data.get('conversation_id')
        if conversation_id:
            room = f"conversation_{conversation_id}"
            user_id = connected_users.get(request.sid)
            emit('user_typing', {
                'user_id': user_id,
                'conversation_id': conversation_id,
            }, room=room, include_self=False)
