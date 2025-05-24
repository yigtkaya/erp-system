"""
API configuration and documentation for the Core module.
This provides centralized settings for API versioning, pagination, and documentation.
"""

# API Versions
API_VERSIONS = {
    'v1': {
        'active': True,
        'deprecated': False,
        'end_of_life': None  # Date when this version will be removed
    },
    'v2': {
        'active': False,
        'deprecated': False,
        'end_of_life': None
    }
}

# Default API version
DEFAULT_VERSION = ''

# API Documentation
MODULE_DESCRIPTION = """
Core API providing authentication, user management, and system-wide functionality.
This module serves as the foundation for the entire ERP system.
"""

ENDPOINT_DESCRIPTIONS = {
    'users': 'Manage system users, their profiles, and permissions.',
    'departments': 'Manage organizational departments and their members.',
    'customers': 'Manage customer records and related information.',
    'audit-logs': 'Access system audit logs for security and compliance.',
    'auth': {
        'login': 'Authenticate users and obtain JWT tokens.',
        'logout': 'Invalidate refresh tokens for secure logout.',
        'permissions': 'Retrieve current user permissions.'
    },
    'dashboard': {
        'overview': 'Get consolidated system metrics and KPIs.',
        'system-metrics': 'Get technical system performance metrics.'
    }
}

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Rate limiting
DEFAULT_THROTTLE_RATES = {
    'anon': '10/minute',
    'user': '60/minute',
    'admin': '120/minute'
}

# API Health and monitoring
HEALTH_CHECK_SERVICES = [
    'database',
    'cache',
    'storage',
    'celery'
] 