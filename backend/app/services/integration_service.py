"""
Integration Service - Manages connections to external APIs.
"""
import logging
import requests
from ..utils.errors import ExternalServiceError

logger = logging.getLogger(__name__)


class IntegrationService:
    """Service for managing external API integrations."""

    def __init__(self):
        self.integrations = {}

    def register_integration(self, name, config):
        """Register a new external integration."""
        self.integrations[name] = {
            'base_url': config.get('base_url', ''),
            'auth_type': config.get('auth_type', 'bearer'),
            'api_key': config.get('api_key', ''),
            'headers': config.get('headers', {}),
            'timeout': config.get('timeout', 30),
            'retry_count': config.get('retry_count', 3),
        }
        logger.info(f"Integration registered: {name}")

    def call_integration(self, name, method, path, data=None, params=None):
        """Make an API call to a registered integration."""
        if name not in self.integrations:
            raise ExternalServiceError(f'Integration "{name}" not registered')

        config = self.integrations[name]
        url = f"{config['base_url']}{path}"
        headers = dict(config['headers'])

        # Add authentication
        if config['auth_type'] == 'bearer' and config['api_key']:
            headers['Authorization'] = f"Bearer {config['api_key']}"
        elif config['auth_type'] == 'api_key' and config['api_key']:
            headers['X-API-Key'] = config['api_key']

        # Retry with exponential backoff
        last_error = None
        for attempt in range(config['retry_count']):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=config['timeout'],
                )

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 2 ** attempt))
                    import time
                    time.sleep(retry_after)
                    continue

                if response.status_code in [401, 403]:
                    raise ExternalServiceError(
                        f'Authentication failed for integration "{name}"'
                    )

                response.raise_for_status()

                return {
                    'status_code': response.status_code,
                    'data': response.json() if response.headers.get(
                        'content-type', ''
                    ).startswith('application/json') else response.text,
                }

            except requests.RequestException as e:
                last_error = e
                if attempt < config['retry_count'] - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff

        raise ExternalServiceError(
            f'Integration "{name}" failed after {config["retry_count"]} attempts: {str(last_error)}'
        )

    def list_integrations(self):
        """List all registered integrations (without sensitive data)."""
        return {
            name: {
                'base_url': config['base_url'],
                'auth_type': config['auth_type'],
                'has_api_key': bool(config['api_key']),
            }
            for name, config in self.integrations.items()
        }


# Singleton instance
integration_service = IntegrationService()
