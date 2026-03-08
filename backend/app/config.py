"""
Application configuration classes for different environments.
"""
import os
from datetime import timedelta


class BaseConfig:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-dev-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers']

    # Bytez AI Configuration
    BYTEZ_API_KEY = os.environ.get('BYTEZ_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'openai/gpt-4o')
    OPENAI_FALLBACK_MODEL = os.environ.get('OPENAI_FALLBACK_MODEL', 'openai/gpt-4o-mini')
    OPENAI_MAX_TOKENS = int(os.environ.get('OPENAI_MAX_TOKENS', 1024))
    OPENAI_TEMPERATURE = float(os.environ.get('OPENAI_TEMPERATURE', 0.7))

    # Context Management
    CONTEXT_WINDOW_SIZE = int(os.environ.get('CONTEXT_WINDOW_SIZE', 20))
    SUMMARY_THRESHOLD = int(os.environ.get('SUMMARY_THRESHOLD', 50))

    # Rate Limiting
    RATELIMIT_DEFAULT = "200/minute"
    RATELIMIT_STORAGE_URI = os.environ.get('REDIS_URL', 'memory://')

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

    # Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///chatbot_dev.db'
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


class StagingConfig(BaseConfig):
    """Staging configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://chatbot:chatbot@localhost:5432/chatbot_staging'
    )


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)

    # Stricter rate limits in production
    RATELIMIT_DEFAULT = "100/minute"


class TestingConfig(BaseConfig):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


config_map = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
