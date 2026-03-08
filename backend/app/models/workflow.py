"""
Workflow and WorkflowRun models for automation engine.
"""
import uuid
import json
from datetime import datetime, timezone
from ..extensions import db


class Workflow(db.Model):
    __tablename__ = 'workflows'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    trigger_config_json = db.Column(db.Text, nullable=False, default='{}')
    steps_json = db.Column(db.Text, nullable=False, default='[]')
    is_active = db.Column(db.Boolean, default=True)
    schedule_cron = db.Column(db.String(100), nullable=True)
    last_run_at = db.Column(db.DateTime, nullable=True)
    run_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    runs = db.relationship('WorkflowRun', backref='workflow', lazy='dynamic',
                           cascade='all, delete-orphan',
                           order_by='WorkflowRun.started_at.desc()')

    TRIGGER_TYPES = ['webhook', 'schedule', 'chat', 'manual', 'event']

    @property
    def trigger_config(self):
        return json.loads(self.trigger_config_json) if self.trigger_config_json else {}

    @trigger_config.setter
    def trigger_config(self, value):
        self.trigger_config_json = json.dumps(value)

    @property
    def steps(self):
        return json.loads(self.steps_json) if self.steps_json else []

    @steps.setter
    def steps(self, value):
        self.steps_json = json.dumps(value)

    def to_dict(self, include_runs=False):
        """Serialize workflow to dictionary."""
        data = {
            'id': self.id,
            'created_by': self.created_by,
            'name': self.name,
            'description': self.description,
            'trigger_config': self.trigger_config,
            'steps': self.steps,
            'is_active': self.is_active,
            'schedule_cron': self.schedule_cron,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'run_count': self.run_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_runs:
            data['recent_runs'] = [run.to_dict() for run in
                                   self.runs.limit(10).all()]
        return data

    def __repr__(self):
        return f'<Workflow {self.name}>'


class WorkflowRun(db.Model):
    __tablename__ = 'workflow_runs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = db.Column(db.String(36), db.ForeignKey('workflows.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    input_data_json = db.Column(db.Text, nullable=True)
    output_data_json = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    step_results_json = db.Column(db.Text, nullable=True, default='[]')
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    VALID_STATUSES = ['pending', 'running', 'completed', 'failed', 'cancelled']

    # Indexes
    __table_args__ = (
        db.Index('idx_run_workflow_started', 'workflow_id', 'started_at'),
        db.Index('idx_run_status', 'status'),
    )

    @property
    def input_data(self):
        return json.loads(self.input_data_json) if self.input_data_json else {}

    @input_data.setter
    def input_data(self, value):
        self.input_data_json = json.dumps(value)

    @property
    def output_data(self):
        return json.loads(self.output_data_json) if self.output_data_json else {}

    @output_data.setter
    def output_data(self, value):
        self.output_data_json = json.dumps(value)

    @property
    def step_results(self):
        return json.loads(self.step_results_json) if self.step_results_json else []

    @step_results.setter
    def step_results(self, value):
        self.step_results_json = json.dumps(value)

    def to_dict(self):
        """Serialize workflow run to dictionary."""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'status': self.status,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'duration_ms': self.duration_ms,
            'step_results': self.step_results,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f'<WorkflowRun {self.id[:8]}... [{self.status}]>'
