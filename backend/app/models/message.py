"""
Message model for storing individual chat messages.
"""
import uuid
from datetime import datetime, timezone
from ..extensions import db


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    tokens_used = db.Column(db.Integer, default=0)
    model = db.Column(db.String(50), nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    VALID_ROLES = ['user', 'assistant', 'system']

    # Indexes
    __table_args__ = (
        db.Index('idx_msg_conv_created', 'conversation_id', 'created_at'),
        db.Index('idx_msg_created', 'created_at'),
    )

    def to_dict(self):
        """Serialize message to dictionary."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'tokens_used': self.tokens_used,
            'model': self.model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<Message {self.id[:8]}... [{self.role}]>'
