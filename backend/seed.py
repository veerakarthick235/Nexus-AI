"""
Database seeder - Creates initial admin user and sample data.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.workflow import Workflow


def seed_database():
    """Seed the database with initial data."""
    app = create_app()

    with app.app_context():
        print("🌱 Seeding database...")

        # Check if admin already exists
        admin = User.query.filter_by(email='admin@chatbot.com').first()
        if admin:
            print("  ⚠️  Admin user already exists, skipping seed.")
            return

        # Create admin user
        admin = User(
            email='admin@chatbot.com',
            username='admin',
            role='admin',
        )
        admin.set_password('admin123!')
        db.session.add(admin)

        # Create operator user
        operator = User(
            email='operator@chatbot.com',
            username='operator',
            role='operator',
        )
        operator.set_password('operator123!')
        db.session.add(operator)

        # Create demo user
        demo_user = User(
            email='demo@chatbot.com',
            username='demo',
            role='chatbot_user',
        )
        demo_user.set_password('demo1234!')
        db.session.add(demo_user)

        db.session.flush()

        # Create sample conversation
        conversation = Conversation(
            user_id=demo_user.id,
            title='Welcome Chat',
        )
        db.session.add(conversation)
        db.session.flush()

        # Add sample messages
        messages = [
            Message(conversation_id=conversation.id, role='user',
                    content='Hello! What can you do?'),
            Message(conversation_id=conversation.id, role='assistant',
                    content='Hello! I\'m your AI assistant. I can help you with:\n\n'
                            '• **Answering questions** on a wide range of topics\n'
                            '• **Creating automation workflows** to streamline your tasks\n'
                            '• **Analyzing data** and providing insights\n'
                            '• **Integrating with external services** like CRM and email\n\n'
                            'How can I help you today?'),
            Message(conversation_id=conversation.id, role='user',
                    content='Can you help me create an automation workflow?'),
            Message(conversation_id=conversation.id, role='assistant',
                    content='Absolutely! I can help you create an automation workflow. '
                            'Here\'s what you can automate:\n\n'
                            '1. **Webhook Triggers** - React to external events\n'
                            '2. **Scheduled Tasks** - Run tasks on a cron schedule\n'
                            '3. **Data Processing** - Transform and route data\n'
                            '4. **Notifications** - Send alerts via email, Slack, or webhooks\n\n'
                            'Would you like to create one? Just go to the Automation tab!'),
        ]
        for msg in messages:
            db.session.add(msg)

        conversation.message_count = len(messages)

        # Create sample workflow
        workflow = Workflow(
            created_by=operator.id,
            name='New User Welcome Email',
            description='Sends a welcome email when a new user registers',
        )
        workflow.trigger_config = {
            'type': 'event',
            'config': {'event': 'user_registered'}
        }
        workflow.steps = [
            {
                'type': 'transform',
                'config': {
                    'template': 'Welcome {{username}}! Thanks for joining our platform.'
                }
            },
            {
                'type': 'notify',
                'config': {
                    'channel': 'log',
                    'target': 'welcome-notifications',
                    'message': 'New user welcome notification sent'
                }
            }
        ]
        db.session.add(workflow)

        # Create another sample workflow
        webhook_workflow = Workflow(
            created_by=operator.id,
            name='Lead Notification',
            description='Notify sales team when a new lead comes in via webhook',
        )
        webhook_workflow.trigger_config = {
            'type': 'webhook',
            'config': {'path': '/hooks/new-lead'}
        }
        webhook_workflow.steps = [
            {
                'type': 'transform',
                'config': {
                    'template': 'New Lead: {{name}} - {{email}} - {{company}}'
                }
            },
            {
                'type': 'condition',
                'config': {
                    'field': 'priority',
                    'operator': 'equals',
                    'value': 'high'
                }
            },
            {
                'type': 'log',
                'config': {
                    'message': 'High priority lead received',
                    'level': 'info'
                }
            }
        ]
        db.session.add(webhook_workflow)

        db.session.commit()
        print("  ✅ Database seeded successfully!")
        print("  📧 Admin: admin@chatbot.com / admin123!")
        print("  📧 Operator: operator@chatbot.com / operator123!")
        print("  📧 Demo: demo@chatbot.com / demo1234!")


if __name__ == '__main__':
    seed_database()
