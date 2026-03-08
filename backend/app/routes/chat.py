"""
Chat routes - Conversations and Messages CRUD + AI responses.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db, limiter
from ..models.conversation import Conversation
from ..models.message import Message
from ..services.ai_service import ai_service
from ..services.analytics_service import analytics_service
from ..utils.errors import NotFoundError, ValidationError
from ..utils.helpers import validate_required_fields, parse_json_body, paginate_query

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/conversations', methods=['POST'])
@jwt_required()
@limiter.limit("30/minute")
def create_conversation():
    """Create a new conversation."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    conversation = Conversation(
        user_id=user_id,
        title=data.get('title', 'New Conversation'),
        system_prompt=data.get('system_prompt'),
    )

    db.session.add(conversation)
    db.session.commit()

    analytics_service.track_event(user_id, 'conversation_created', {
        'conversation_id': conversation.id,
    })

    return jsonify({
        'conversation': conversation.to_dict(),
    }), 201


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    """List all conversations for the current user."""
    user_id = get_jwt_identity()
    query = (
        Conversation.query
        .filter_by(user_id=user_id, is_archived=False)
        .order_by(Conversation.updated_at.desc())
    )

    result = paginate_query(query)
    return jsonify(result), 200


@chat_bp.route('/conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(conversation_id):
    """Get a conversation with its messages."""
    user_id = get_jwt_identity()
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=user_id
    ).first()

    if not conversation:
        raise NotFoundError('Conversation not found')

    # Get messages with pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    messages_query = (
        Message.query
        .filter_by(conversation_id=conversation_id)
        .order_by(Message.created_at.asc())
    )

    pagination = messages_query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'conversation': conversation.to_dict(),
        'messages': [msg.to_dict() for msg in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        }
    }), 200


@chat_bp.route('/conversations/<conversation_id>/messages', methods=['POST'])
@jwt_required()
@limiter.limit("30/minute")
def send_message(conversation_id):
    """Send a message and get an AI response."""
    user_id = get_jwt_identity()
    data = parse_json_body()
    validate_required_fields(data, ['content'])

    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=user_id
    ).first()

    if not conversation:
        raise NotFoundError('Conversation not found')

    content = data['content'].strip()
    if not content:
        raise ValidationError('Message content cannot be empty')

    # Store user message
    user_message = Message(
        conversation_id=conversation_id,
        role='user',
        content=content,
    )
    db.session.add(user_message)
    conversation.message_count = (conversation.message_count or 0) + 1

    # Generate title for new conversations
    if conversation.message_count <= 1:
        conversation.title = ai_service.generate_conversation_title(content)

    db.session.commit()

    # Track event
    analytics_service.track_event(user_id, 'chat_message_sent', {
        'conversation_id': conversation_id,
    })

    # Generate AI response
    ai_response = ai_service.generate_response(conversation_id, content)

    # Store assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role='assistant',
        content=ai_response['content'],
        tokens_used=ai_response.get('tokens_used', 0),
        model=ai_response.get('model', ''),
    )
    db.session.add(assistant_message)
    conversation.message_count = (conversation.message_count or 0) + 1
    conversation.total_tokens = (conversation.total_tokens or 0) + ai_response.get('tokens_used', 0)
    db.session.commit()

    # Track event
    analytics_service.track_event(user_id, 'chat_message_received', {
        'conversation_id': conversation_id,
        'tokens_used': ai_response.get('tokens_used', 0),
    })

    # Check if summarization needed
    summary_threshold = 50
    if conversation.message_count >= summary_threshold and not conversation.summary:
        try:
            ai_service.summarize_conversation(conversation_id)
        except Exception as e:
            logger.warning(f"Failed to summarize conversation: {e}")

    return jsonify({
        'user_message': user_message.to_dict(),
        'assistant_message': assistant_message.to_dict(),
    }), 200


@chat_bp.route('/conversations/<conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(conversation_id):
    """Delete a conversation and all its messages."""
    user_id = get_jwt_identity()
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=user_id
    ).first()

    if not conversation:
        raise NotFoundError('Conversation not found')

    db.session.delete(conversation)
    db.session.commit()

    return jsonify({'message': 'Conversation deleted'}), 200


@chat_bp.route('/conversations/<conversation_id>/archive', methods=['POST'])
@jwt_required()
def archive_conversation(conversation_id):
    """Archive a conversation."""
    user_id = get_jwt_identity()
    conversation = Conversation.query.filter_by(
        id=conversation_id, user_id=user_id
    ).first()

    if not conversation:
        raise NotFoundError('Conversation not found')

    conversation.is_archived = True
    db.session.commit()

    analytics_service.track_event(user_id, 'conversation_archived', {
        'conversation_id': conversation_id,
    })

    return jsonify({
        'message': 'Conversation archived',
        'conversation': conversation.to_dict(),
    }), 200
