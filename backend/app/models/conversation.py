"""
Conversation model for organizing chat sessions.
"""
import uuid
from datetime import datetime, timezone
from ..extensions import db


class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), default='New Conversation')
    system_prompt = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)  # JSON string for SQLite compat
    is_archived = db.Column(db.Boolean, default=False)
    summary = db.Column(db.Text, nullable=True)
    message_count = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    messages = db.relationship('Message', backref='conversation', lazy='dynamic',
                               cascade='all, delete-orphan',
                               order_by='Message.created_at')

    # Indexes
    __table_args__ = (
        db.Index('idx_conv_user_updated', 'user_id', 'updated_at'),
    )

    def to_dict(self, include_messages=False):
        """Serialize conversation to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'is_archived': self.is_archived,
            'message_count': self.message_count,
            'total_tokens': self.total_tokens,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in
                                self.messages.order_by('created_at').all()]
        return data

    def __repr__(self):
        return f'<Conversation {self.id[:8]}... - {self.title}>'
