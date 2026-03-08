"""
AnalyticsEvent model for tracking user interactions and system events.
"""
import uuid
import json
from datetime import datetime, timezone
from ..extensions import db


class AnalyticsEvent(db.Model):
    __tablename__ = 'analytics_events'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    event_data_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    EVENT_TYPES = [
        'chat_message_sent', 'chat_message_received',
        'conversation_created', 'conversation_archived',
        'workflow_triggered', 'workflow_completed', 'workflow_failed',
        'user_login', 'user_registered',
        'api_key_created', 'api_key_revoked',
    ]

    # Indexes
    __table_args__ = (
        db.Index('idx_event_type_created', 'event_type', 'created_at'),
        db.Index('idx_event_user_created', 'user_id', 'created_at'),
    )

    @property
    def event_data(self):
        return json.loads(self.event_data_json) if self.event_data_json else {}

    @event_data.setter
    def event_data(self, value):
        self.event_data_json = json.dumps(value)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<AnalyticsEvent {self.event_type}>'
