"""
AI Chatbot & Automation Platform - Flask Application Factory
"""
import os
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from .extensions import db, migrate, jwt, limiter, socketio
from .config import config_map


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['development']))

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}})
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.chat import chat_bp
    from .routes.automation import automation_bp
    from .routes.users import users_bp
    from .routes.analytics import analytics_bp
    from .routes.health import health_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(automation_bp, url_prefix='/api/automation')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(health_bp)

    # Register error handlers
    from .utils.errors import register_error_handlers
    register_error_handlers(app)

    # Register WebSocket events
    from .services.websocket_service import register_socket_events
    register_socket_events(socketio)

    # Create tables
    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    return app
