"""
Analytics routes - Dashboard metrics and reporting.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..services.analytics_service import analytics_service
from ..utils.helpers import require_roles

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/overview', methods=['GET'])
@jwt_required()
@require_roles('admin', 'operator')
def get_overview():
    """Get dashboard overview metrics."""
    days = request.args.get('days', 30, type=int)
    data = analytics_service.get_overview(days)
    return jsonify(data), 200


@analytics_bp.route('/conversations', methods=['GET'])
@jwt_required()
@require_roles('admin', 'operator')
def get_conversation_analytics():
    """Get conversation analytics."""
    days = request.args.get('days', 30, type=int)
    data = analytics_service.get_conversation_analytics(days)
    return jsonify(data), 200


@analytics_bp.route('/automations', methods=['GET'])
@jwt_required()
@require_roles('admin', 'operator')
def get_automation_analytics():
    """Get automation analytics."""
    days = request.args.get('days', 30, type=int)
    data = analytics_service.get_automation_analytics(days)
    return jsonify(data), 200


@analytics_bp.route('/users', methods=['GET'])
@jwt_required()
@require_roles('admin')
def get_user_analytics():
    """Get user engagement analytics (admin only)."""
    days = request.args.get('days', 30, type=int)
    data = analytics_service.get_user_analytics(days)
    return jsonify(data), 200
