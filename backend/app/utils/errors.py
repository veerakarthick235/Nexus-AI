"""
Standardized error handling for the application.
"""
from flask import jsonify
import traceback
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base API error class."""

    def __init__(self, message, code='INTERNAL_ERROR', status_code=500, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class ValidationError(APIError):
    def __init__(self, message='Invalid request data', details=None):
        super().__init__(message, 'VALIDATION_ERROR', 400, details)


class AuthenticationError(APIError):
    def __init__(self, message='Authentication required'):
        super().__init__(message, 'UNAUTHORIZED', 401)


class AuthorizationError(APIError):
    def __init__(self, message='Insufficient permissions'):
        super().__init__(message, 'FORBIDDEN', 403)


class NotFoundError(APIError):
    def __init__(self, message='Resource not found'):
        super().__init__(message, 'NOT_FOUND', 404)


class RateLimitError(APIError):
    def __init__(self, message='Too many requests'):
        super().__init__(message, 'RATE_LIMITED', 429)


class AIServiceError(APIError):
    def __init__(self, message='AI service unavailable'):
        super().__init__(message, 'AI_SERVICE_ERROR', 502)


class ExternalServiceError(APIError):
    def __init__(self, message='External service error', details=None):
        super().__init__(message, 'EXTERNAL_SERVICE_ERROR', 502, details)


def format_error_response(error_code, message, details=None, request_id=None):
    """Format a standardized error response."""
    response = {
        'error': {
            'code': error_code,
            'message': message,
        }
    }
    if details:
        response['error']['details'] = details
    if request_id:
        response['error']['request_id'] = request_id
    return response


def register_error_handlers(app):
    """Register global error handlers with the Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = format_error_response(error.code, error.message, error.details)
        return jsonify(response), error.status_code

    @app.errorhandler(400)
    def handle_bad_request(error):
        response = format_error_response('VALIDATION_ERROR', 'Bad request')
        return jsonify(response), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        response = format_error_response('NOT_FOUND', 'Resource not found')
        return jsonify(response), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        response = format_error_response('METHOD_NOT_ALLOWED', 'Method not allowed')
        return jsonify(response), 405

    @app.errorhandler(429)
    def handle_rate_limit(error):
        response = format_error_response('RATE_LIMITED', 'Too many requests')
        return jsonify(response), 429

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {traceback.format_exc()}")
        response = format_error_response('INTERNAL_ERROR', 'An unexpected error occurred')
        return jsonify(response), 500
