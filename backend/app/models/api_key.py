"""
API Key model for programmatic access.
"""
import uuid
import hashlib
import secrets
from datetime import datetime, timezone
from ..extensions import db


class APIKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(64), unique=True, nullable=False)
    key_prefix = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    scopes = db.Column(db.String(500), nullable=True, default='')
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def generate_key():
        """Generate a new API key and return (raw_key, key_hash, key_prefix)."""
        raw_key = f"cb_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:10]
        return raw_key, key_hash, key_prefix

    @staticmethod
    def hash_key(raw_key):
        """Hash a raw API key for lookup."""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def has_scope(self, scope):
        """Check if this key has a specific scope."""
        if not self.scopes:
            return False
        return scope in self.scopes.split(',')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'key_prefix': self.key_prefix,
            'scopes': self.scopes.split(',') if self.scopes else [],
            'is_active': self.is_active,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
