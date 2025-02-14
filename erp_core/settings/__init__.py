"""
Django settings module initialization.
"""

import os

# Load the appropriate settings based on DJANGO_SETTINGS_MODULE environment variable
environment = os.getenv('DJANGO_SETTINGS_MODULE', 'erp_core.settings.development')

if environment == 'erp_core.settings.production':
    from .production import *
else:
    from .development import * 