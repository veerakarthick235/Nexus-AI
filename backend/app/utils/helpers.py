"""
Utility helper functions.
"""
import uuid
import json
from datetime import datetime, timezone
from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from ..models.user import User
from ..utils.errors import AuthorizationError, ValidationError


def generate_id():
    """Generate a UUID string."""
    return str(uuid.uuid4())


def utc_now():
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def require_roles(*roles):
    """Decorator to require specific user roles for an endpoint."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            if not user:
                raise AuthorizationError('User not found')
            if not user.has_role(*roles):
                raise AuthorizationError(
                    f'This action requires one of the following roles: {", ".join(roles)}'
                )
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_required_fields(data, required_fields):
    """Validate that required fields are present in the request data."""
    missing = [f for f in required_fields if f not in data or data[f] is None]
    if missing:
        details = [{'field': f, 'issue': 'Field is required'} for f in missing]
        raise ValidationError('Missing required fields', details)


def paginate_query(query, page=None, per_page=None, max_per_page=100):
    """Apply pagination to a SQLAlchemy query."""
    if page is None:
        page = request.args.get('page', 1, type=int)
    if per_page is None:
        per_page = request.args.get('per_page', 20, type=int)

    per_page = min(per_page, max_per_page)
    page = max(page, 1)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items': [item.to_dict() for item in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total_pages': pagination.pages,
            'total_items': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        }
    }


def parse_json_body():
    """Parse and return JSON request body, raising error if invalid."""
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError('Request body must be valid JSON')
    return data
