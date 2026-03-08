"""
Analytics Service - Aggregation and reporting of platform metrics.
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from ..extensions import db
from ..models.analytics import AnalyticsEvent
from ..models.conversation import Conversation
from ..models.message import Message
from ..models.workflow import Workflow, WorkflowRun
from ..models.user import User

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for computing analytics metrics."""

    def get_overview(self, days=30):
        """Get dashboard overview metrics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        total_users = User.query.filter_by(is_active=True).count()
        total_conversations = Conversation.query.filter(
            Conversation.created_at >= cutoff
        ).count()
        total_messages = Message.query.filter(
            Message.created_at >= cutoff
        ).count()
        total_workflow_runs = WorkflowRun.query.filter(
            WorkflowRun.started_at >= cutoff
        ).count()
        successful_runs = WorkflowRun.query.filter(
            WorkflowRun.started_at >= cutoff,
            WorkflowRun.status == 'completed'
        ).count()
        failed_runs = WorkflowRun.query.filter(
            WorkflowRun.started_at >= cutoff,
            WorkflowRun.status == 'failed'
        ).count()

        # Average messages per conversation
        avg_messages = 0
        if total_conversations > 0:
            avg_messages = round(total_messages / total_conversations, 1)

        # Automation success rate
        success_rate = 0
        if total_workflow_runs > 0:
            success_rate = round((successful_runs / total_workflow_runs) * 100, 1)

        return {
            'period_days': days,
            'total_users': total_users,
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'avg_messages_per_conversation': avg_messages,
            'total_workflow_runs': total_workflow_runs,
            'successful_runs': successful_runs,
            'failed_runs': failed_runs,
            'automation_success_rate': success_rate,
        }

    def get_conversation_analytics(self, days=30):
        """Get conversation-specific analytics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Daily conversation counts
        daily_conversations = (
            db.session.query(
                func.date(Conversation.created_at).label('date'),
                func.count(Conversation.id).label('count')
            )
            .filter(Conversation.created_at >= cutoff)
            .group_by(func.date(Conversation.created_at))
            .all()
        )

        # Daily message counts
        daily_messages = (
            db.session.query(
                func.date(Message.created_at).label('date'),
                func.count(Message.id).label('count')
            )
            .filter(Message.created_at >= cutoff)
            .group_by(func.date(Message.created_at))
            .all()
        )

        # Token usage
        total_tokens = db.session.query(
            func.sum(Message.tokens_used)
        ).filter(
            Message.created_at >= cutoff,
            Message.role == 'assistant'
        ).scalar() or 0

        return {
            'daily_conversations': [
                {'date': str(row.date), 'count': row.count}
                for row in daily_conversations
            ],
            'daily_messages': [
                {'date': str(row.date), 'count': row.count}
                for row in daily_messages
            ],
            'total_tokens_used': total_tokens,
        }

    def get_automation_analytics(self, days=30):
        """Get automation-specific analytics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Workflow run statistics
        runs_by_status = (
            db.session.query(
                WorkflowRun.status,
                func.count(WorkflowRun.id).label('count')
            )
            .filter(WorkflowRun.started_at >= cutoff)
            .group_by(WorkflowRun.status)
            .all()
        )

        # Average run duration
        avg_duration = db.session.query(
            func.avg(WorkflowRun.duration_ms)
        ).filter(
            WorkflowRun.started_at >= cutoff,
            WorkflowRun.status == 'completed'
        ).scalar() or 0

        # Top workflows by run count
        top_workflows = (
            db.session.query(
                Workflow.name,
                func.count(WorkflowRun.id).label('run_count')
            )
            .join(WorkflowRun)
            .filter(WorkflowRun.started_at >= cutoff)
            .group_by(Workflow.name)
            .order_by(func.count(WorkflowRun.id).desc())
            .limit(10)
            .all()
        )

        return {
            'runs_by_status': {row.status: row.count for row in runs_by_status},
            'avg_duration_ms': round(float(avg_duration), 0),
            'top_workflows': [
                {'name': row.name, 'run_count': row.run_count}
                for row in top_workflows
            ],
        }

    def get_user_analytics(self, days=30):
        """Get user engagement analytics."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # New users
        new_users = User.query.filter(User.created_at >= cutoff).count()

        # Most active users (by message count)
        active_users = (
            db.session.query(
                User.username,
                func.count(Message.id).label('message_count')
            )
            .join(Conversation, User.id == Conversation.user_id)
            .join(Message, Conversation.id == Message.conversation_id)
            .filter(Message.created_at >= cutoff, Message.role == 'user')
            .group_by(User.username)
            .order_by(func.count(Message.id).desc())
            .limit(10)
            .all()
        )

        # Users by role
        users_by_role = (
            db.session.query(
                User.role,
                func.count(User.id).label('count')
            )
            .filter(User.is_active == True)  # noqa: E712
            .group_by(User.role)
            .all()
        )

        return {
            'new_users': new_users,
            'active_users': [
                {'username': row.username, 'message_count': row.message_count}
                for row in active_users
            ],
            'users_by_role': {row.role: row.count for row in users_by_role},
        }

    def track_event(self, user_id, event_type, event_data=None):
        """Record an analytics event."""
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
        )
        if event_data:
            event.event_data = event_data

        db.session.add(event)
        db.session.commit()
        return event


# Singleton instance
analytics_service = AnalyticsService()
