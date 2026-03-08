"""
Automation routes - Workflow CRUD and execution.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db, limiter
from ..models.workflow import Workflow, WorkflowRun
from ..services.automation_service import automation_service
from ..utils.errors import NotFoundError
from ..utils.helpers import (
    require_roles, validate_required_fields,
    parse_json_body, paginate_query
)

logger = logging.getLogger(__name__)
automation_bp = Blueprint('automation', __name__)


@automation_bp.route('/workflows', methods=['POST'])
@jwt_required()
@require_roles('admin', 'operator')
@limiter.limit("60/minute")
def create_workflow():
    """Create a new automation workflow."""
    user_id = get_jwt_identity()
    data = parse_json_body()
    validate_required_fields(data, ['name'])

    workflow = automation_service.create_workflow(user_id, data)

    return jsonify({
        'message': 'Workflow created successfully',
        'workflow': workflow.to_dict(),
    }), 201


@automation_bp.route('/workflows', methods=['GET'])
@jwt_required()
def list_workflows():
    """List all workflows."""
    user_id = get_jwt_identity()
    show_all = request.args.get('all', 'false').lower() == 'true'

    query = Workflow.query.order_by(Workflow.updated_at.desc())

    if not show_all:
        query = query.filter_by(created_by=user_id)

    result = paginate_query(query)
    return jsonify(result), 200


@automation_bp.route('/workflows/<workflow_id>', methods=['GET'])
@jwt_required()
def get_workflow(workflow_id):
    """Get a specific workflow with recent runs."""
    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        raise NotFoundError('Workflow not found')

    return jsonify({
        'workflow': workflow.to_dict(include_runs=True),
    }), 200


@automation_bp.route('/workflows/<workflow_id>', methods=['PUT'])
@jwt_required()
@require_roles('admin', 'operator')
def update_workflow(workflow_id):
    """Update an existing workflow."""
    data = parse_json_body()
    workflow = automation_service.update_workflow(workflow_id, data)

    return jsonify({
        'message': 'Workflow updated successfully',
        'workflow': workflow.to_dict(),
    }), 200


@automation_bp.route('/workflows/<workflow_id>', methods=['DELETE'])
@jwt_required()
@require_roles('admin')
def delete_workflow(workflow_id):
    """Delete a workflow."""
    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        raise NotFoundError('Workflow not found')

    db.session.delete(workflow)
    db.session.commit()

    return jsonify({'message': 'Workflow deleted'}), 200


@automation_bp.route('/workflows/<workflow_id>/trigger', methods=['POST'])
@jwt_required()
@require_roles('admin', 'operator')
@limiter.limit("60/minute")
def trigger_workflow(workflow_id):
    """Manually trigger a workflow execution."""
    data = request.get_json(silent=True) or {}
    input_data = data.get('input_data', {})

    run = automation_service.trigger_workflow(workflow_id, input_data)

    return jsonify({
        'message': f'Workflow triggered - status: {run.status}',
        'run': run.to_dict(),
    }), 200


@automation_bp.route('/workflows/<workflow_id>/runs', methods=['GET'])
@jwt_required()
def get_workflow_runs(workflow_id):
    """Get execution history for a workflow."""
    workflow = Workflow.query.get(workflow_id)
    if not workflow:
        raise NotFoundError('Workflow not found')

    query = (
        WorkflowRun.query
        .filter_by(workflow_id=workflow_id)
        .order_by(WorkflowRun.started_at.desc())
    )

    result = paginate_query(query)
    return jsonify(result), 200


# Webhook endpoint for external triggers
@automation_bp.route('/hooks/<path:hook_path>', methods=['POST'])
@limiter.limit("60/minute")
def handle_webhook(hook_path):
    """Handle incoming webhook triggers."""
    data = request.get_json(silent=True) or {}

    # Find workflows with matching webhook path
    workflows = Workflow.query.filter_by(is_active=True).all()
    triggered = []

    for workflow in workflows:
        trigger = workflow.trigger_config
        if trigger.get('type') == 'webhook' and trigger.get('config', {}).get('path') == f'/hooks/{hook_path}':
            run = automation_service.trigger_workflow(workflow.id, data)
            triggered.append({
                'workflow_id': workflow.id,
                'workflow_name': workflow.name,
                'run_id': run.id,
                'status': run.status,
            })

    if not triggered:
        return jsonify({
            'message': 'No workflows matched this webhook path',
            'path': hook_path,
        }), 200

    return jsonify({
        'message': f'{len(triggered)} workflow(s) triggered',
        'triggered': triggered,
    }), 200
