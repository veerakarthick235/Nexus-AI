"""
Automation Service - Handles workflow creation, execution, and management.
"""
import json
import logging
import time
import requests
from datetime import datetime, timezone
from ..extensions import db
from ..models.workflow import Workflow, WorkflowRun
from ..models.analytics import AnalyticsEvent
from ..utils.errors import NotFoundError, ValidationError, ExternalServiceError

logger = logging.getLogger(__name__)


class AutomationService:
    """Service for managing and executing automation workflows."""

    STEP_HANDLERS = {}

    def __init__(self):
        self._register_step_handlers()

    def _register_step_handlers(self):
        """Register built-in step type handlers."""
        self.STEP_HANDLERS = {
            'transform': self._execute_transform_step,
            'api_call': self._execute_api_call_step,
            'notify': self._execute_notify_step,
            'condition': self._execute_condition_step,
            'delay': self._execute_delay_step,
            'ai_process': self._execute_ai_process_step,
            'log': self._execute_log_step,
        }

    def create_workflow(self, user_id, data):
        """Create a new automation workflow."""
        workflow = Workflow(
            created_by=user_id,
            name=data['name'],
            description=data.get('description', ''),
            schedule_cron=data.get('schedule_cron'),
        )
        workflow.trigger_config = data.get('trigger', {})
        workflow.steps = data.get('steps', [])
        workflow.is_active = data.get('is_active', True)

        db.session.add(workflow)
        db.session.commit()

        logger.info(f"Workflow created: {workflow.id} - {workflow.name}")
        return workflow

    def update_workflow(self, workflow_id, data):
        """Update an existing workflow."""
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            raise NotFoundError('Workflow not found')

        if 'name' in data:
            workflow.name = data['name']
        if 'description' in data:
            workflow.description = data['description']
        if 'trigger' in data:
            workflow.trigger_config = data['trigger']
        if 'steps' in data:
            workflow.steps = data['steps']
        if 'is_active' in data:
            workflow.is_active = data['is_active']
        if 'schedule_cron' in data:
            workflow.schedule_cron = data['schedule_cron']

        db.session.commit()
        return workflow

    def trigger_workflow(self, workflow_id, input_data=None):
        """Trigger a workflow execution."""
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            raise NotFoundError('Workflow not found')
        if not workflow.is_active:
            raise ValidationError('Workflow is not active')

        # Create a run record
        run = WorkflowRun(
            workflow_id=workflow_id,
            status='running',
        )
        run.input_data = input_data or {}
        db.session.add(run)
        db.session.commit()

        # Execute the workflow
        try:
            result = self._execute_workflow(workflow, run)
            run.status = 'completed'
            run.output_data = result
            run.completed_at = datetime.now(timezone.utc)
            run.duration_ms = int(
                (run.completed_at - run.started_at).total_seconds() * 1000
            )

            # Update workflow stats
            workflow.last_run_at = run.completed_at
            workflow.run_count = (workflow.run_count or 0) + 1

            # Log analytics event
            event = AnalyticsEvent(
                user_id=workflow.created_by,
                event_type='workflow_completed',
            )
            event.event_data = {
                'workflow_id': workflow_id,
                'run_id': run.id,
                'duration_ms': run.duration_ms,
            }
            db.session.add(event)
            db.session.commit()

            logger.info(f"Workflow {workflow_id} completed in {run.duration_ms}ms")
            return run

        except Exception as e:
            run.status = 'failed'
            run.error_message = str(e)
            run.completed_at = datetime.now(timezone.utc)
            run.duration_ms = int(
                (run.completed_at - run.started_at).total_seconds() * 1000
            )

            # Log failure event
            event = AnalyticsEvent(
                user_id=workflow.created_by,
                event_type='workflow_failed',
            )
            event.event_data = {
                'workflow_id': workflow_id,
                'run_id': run.id,
                'error': str(e),
            }
            db.session.add(event)
            db.session.commit()

            logger.error(f"Workflow {workflow_id} failed: {e}")
            return run

    def _execute_workflow(self, workflow, run):
        """Execute all steps in a workflow sequentially."""
        steps = workflow.steps
        context = {
            'input': run.input_data,
            'results': [],
            'variables': {},
        }

        for i, step in enumerate(steps):
            step_type = step.get('type')
            step_config = step.get('config', {})

            handler = self.STEP_HANDLERS.get(step_type)
            if not handler:
                raise ValidationError(f'Unknown step type: {step_type}')

            logger.info(f"Executing step {i+1}/{len(steps)}: {step_type}")

            try:
                result = handler(step_config, context)
                step_result = {
                    'step_index': i,
                    'step_type': step_type,
                    'status': 'completed',
                    'result': result,
                }
            except Exception as e:
                step_result = {
                    'step_index': i,
                    'step_type': step_type,
                    'status': 'failed',
                    'error': str(e),
                }
                context['results'].append(step_result)
                run.step_results = context['results']
                raise

            context['results'].append(step_result)
            context['variables'][f'step_{i}_result'] = result

        run.step_results = context['results']
        return {
            'steps_completed': len(steps),
            'final_result': context['results'][-1] if context['results'] else None,
        }

    def _execute_transform_step(self, config, context):
        """Transform data using a template."""
        template = config.get('template', '')
        data = context.get('input', {})

        # Simple template substitution
        result = template
        for key, value in data.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))
            result = result.replace(f'{{{{data.{key}}}}}', str(value))

        return {'transformed': result}

    def _execute_api_call_step(self, config, context):
        """Make an HTTP API call."""
        url = config.get('url', '')
        method = config.get('method', 'GET').upper()
        headers = config.get('headers', {})
        body = config.get('body', {})
        timeout = config.get('timeout', 30)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body if method in ['POST', 'PUT', 'PATCH'] else None,
                params=body if method == 'GET' else None,
                timeout=timeout,
            )
            return {
                'status_code': response.status_code,
                'body': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            }
        except requests.RequestException as e:
            raise ExternalServiceError(f'API call failed: {str(e)}')

    def _execute_notify_step(self, config, context):
        """Send a notification (email, slack, webhook)."""
        channel = config.get('channel', 'log')
        message = config.get('message', '')
        target = config.get('target', '')

        if channel == 'webhook':
            try:
                response = requests.post(target, json={'message': message}, timeout=10)
                return {'sent': True, 'status_code': response.status_code}
            except requests.RequestException as e:
                raise ExternalServiceError(f'Notification webhook failed: {str(e)}')

        elif channel == 'log':
            logger.info(f"NOTIFICATION [{target}]: {message}")
            return {'sent': True, 'channel': 'log'}

        else:
            # Placeholder for email/slack integrations
            logger.info(f"NOTIFICATION [{channel}:{target}]: {message}")
            return {'sent': True, 'channel': channel, 'note': 'Integration pending'}

    def _execute_condition_step(self, config, context):
        """Evaluate a condition and determine the next path."""
        field = config.get('field', '')
        operator = config.get('operator', 'equals')
        value = config.get('value', '')

        # Get the actual value from context
        actual = context.get('input', {}).get(field)
        if actual is None:
            for result in context.get('results', []):
                r = result.get('result', {})
                if isinstance(r, dict) and field in r:
                    actual = r[field]
                    break

        # Evaluate condition
        condition_met = False
        if operator == 'equals':
            condition_met = str(actual) == str(value)
        elif operator == 'not_equals':
            condition_met = str(actual) != str(value)
        elif operator == 'greater_than':
            condition_met = float(actual or 0) > float(value)
        elif operator == 'less_than':
            condition_met = float(actual or 0) < float(value)
        elif operator == 'contains':
            condition_met = str(value) in str(actual or '')

        return {
            'condition_met': condition_met,
            'field': field,
            'operator': operator,
            'expected': value,
            'actual': actual,
        }

    def _execute_delay_step(self, config, context):
        """Wait for a specified duration."""
        seconds = config.get('seconds', 0)
        max_delay = 300  # 5 minutes max
        seconds = min(seconds, max_delay)

        if seconds > 0:
            time.sleep(seconds)

        return {'delayed_seconds': seconds}

    def _execute_ai_process_step(self, config, context):
        """Process data through the AI model."""
        from .ai_service import ai_service
        prompt = config.get('prompt', '')
        input_data = context.get('input', {})

        # Inject context data into prompt
        for key, value in input_data.items():
            prompt = prompt.replace(f'{{{{{key}}}}}', str(value))

        try:
            result = ai_service.generate_response(
                conversation_id=None,
                user_message_content=prompt,
            )
            return {
                'ai_response': result.get('content', ''),
                'model': result.get('model', ''),
            }
        except Exception as e:
            return {
                'ai_response': f'AI processing failed: {str(e)}',
                'error': True,
            }

    def _execute_log_step(self, config, context):
        """Log a message with context data."""
        message = config.get('message', 'Log step executed')
        level = config.get('level', 'info')

        log_func = getattr(logger, level, logger.info)
        log_func(f"WORKFLOW LOG: {message}")

        return {'logged': True, 'message': message}


# Singleton instance
automation_service = AutomationService()
