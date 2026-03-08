"""
Authentication routes - Register, Login, Refresh, Logout.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from ..extensions import db, limiter
from ..models.user import User
from ..services.analytics_service import analytics_service
from ..utils.errors import ValidationError, AuthenticationError
from ..utils.helpers import validate_required_fields, parse_json_body

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10/minute")
def register():
    """Register a new user."""
    data = parse_json_body()
    validate_required_fields(data, ['email', 'username', 'password'])

    email = data['email'].lower().strip()
    username = data['username'].strip()
    password = data['password']

    # Validation
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters', [
            {'field': 'password', 'issue': 'Too short (min 8 characters)'}
        ])

    if User.query.filter_by(email=email).first():
        raise ValidationError('Email already registered', [
            {'field': 'email', 'issue': 'Already in use'}
        ])

    if User.query.filter_by(username=username).first():
        raise ValidationError('Username already taken', [
            {'field': 'username', 'issue': 'Already in use'}
        ])

    # Create user
    user = User(
        email=email,
        username=username,
        role=data.get('role', 'chatbot_user'),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Track event
    analytics_service.track_event(user.id, 'user_registered')

    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    logger.info(f"User registered: {username} ({email})")

    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(include_email=True),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10/minute")
def login():
    """Authenticate user and return tokens."""
    data = parse_json_body()
    validate_required_fields(data, ['email', 'password'])

    email = data['email'].lower().strip()
    password = data['password']

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        raise AuthenticationError('Invalid email or password')

    if not user.is_active:
        raise AuthenticationError('Account has been deactivated')

    # Generate tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    # Track event
    analytics_service.track_event(user.id, 'user_login')

    logger.info(f"User logged in: {user.username}")

    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(include_email=True),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh the access token."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_active:
        raise AuthenticationError('User not found or inactive')

    access_token = create_access_token(identity=user_id)

    return jsonify({
        'access_token': access_token,
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout (invalidate token)."""
    # In a production setup, you'd add the token to a blacklist in Redis
    return jsonify({'message': 'Successfully logged out'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get the current authenticated user's profile."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        raise AuthenticationError('User not found')

    return jsonify({
        'user': user.to_dict(include_email=True),
    }), 200
