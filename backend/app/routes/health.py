"""
Health check routes for monitoring.
"""
from flask import Blueprint, jsonify
from ..extensions import db

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check."""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Chatbot & Automation Platform',
    }), 200


@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check - verifies database connectivity."""
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'

    ready = db_status == 'connected'

    return jsonify({
        'status': 'ready' if ready else 'not_ready',
        'checks': {
            'database': db_status,
        },
    }), 200 if ready else 503
