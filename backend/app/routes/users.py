"""
User management routes.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..utils.errors import NotFoundError, ValidationError, AuthorizationError
from ..utils.helpers import require_roles, parse_json_body, paginate_query

logger = logging.getLogger(__name__)
users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
@jwt_required()
@require_roles('admin')
def list_users():
    """List all users (admin only)."""
    query = User.query.order_by(User.created_at.desc())

    # Filter by role
    role = request.args.get('role')
    if role:
        query = query.filter_by(role=role)

    # Filter by active status
    active = request.args.get('active')
    if active is not None:
        query = query.filter_by(is_active=active.lower() == 'true')

    # Search by username or email
    search = request.args.get('search')
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )

    result = paginate_query(query)
    # Include email for admin view
    result['items'] = [
        User.query.get(item['id']).to_dict(include_email=True)
        for item in result['items']
    ]

    return jsonify(result), 200


@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get a user's profile."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')

    # Users can view their own profile; admins can view any profile
    include_email = (user_id == current_user_id or current_user.has_role('admin'))

    return jsonify({
        'user': user.to_dict(include_email=include_email),
    }), 200


@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update a user's profile."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Only the user themselves or an admin can update
    if user_id != current_user_id and not current_user.has_role('admin'):
        raise AuthorizationError('Cannot update other users')

    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')

    data = parse_json_body()

    if 'username' in data:
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != user_id:
            raise ValidationError('Username already taken')
        user.username = data['username']

    if 'email' in data:
        existing = User.query.filter_by(email=data['email'].lower()).first()
        if existing and existing.id != user_id:
            raise ValidationError('Email already in use')
        user.email = data['email'].lower()

    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']

    if 'password' in data:
        if len(data['password']) < 8:
            raise ValidationError('Password must be at least 8 characters')
        user.set_password(data['password'])

    # Only admins can change roles
    if 'role' in data and current_user.has_role('admin'):
        if data['role'] not in User.VALID_ROLES:
            raise ValidationError(f'Invalid role. Valid roles: {", ".join(User.VALID_ROLES)}')
        user.role = data['role']

    db.session.commit()

    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict(include_email=True),
    }), 200


@users_bp.route('/<user_id>', methods=['DELETE'])
@jwt_required()
@require_roles('admin')
def deactivate_user(user_id):
    """Deactivate a user (admin only)."""
    current_user_id = get_jwt_identity()

    if user_id == current_user_id:
        raise ValidationError('Cannot deactivate your own account')

    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('User not found')

    user.is_active = False
    db.session.commit()

    return jsonify({
        'message': 'User deactivated',
        'user': user.to_dict(),
    }), 200
