"""
Cloudflare R2 settings for ERP System project.
"""

import os
from pathlib import Path

# Cloudflare R2 Settings
AWS_ACCESS_KEY_ID = os.getenv('CLOUDFLARE_R2_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('CLOUDFLARE_R2_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('CLOUDFLARE_R2_ENDPOINT_URL')  # e.g., https://<account_id>.r2.cloudflarestorage.com
AWS_S3_REGION_NAME = os.getenv('CLOUDFLARE_R2_REGION_NAME', 'auto')  # Cloudflare R2 uses 'auto'

# Optional: If you want to use a custom domain for your R2 bucket
AWS_S3_CUSTOM_DOMAIN = os.getenv('CLOUDFLARE_R2_CUSTOM_DOMAIN', None)

# Storage settings
STATICFILES_LOCATION = 'static'
MEDIAFILES_LOCATION = 'media'

# Default ACL for Cloudflare R2 (usually 'private' or None)
# Cloudflare R2 doesn't support ACLs in the same way as AWS S3
AWS_DEFAULT_ACL = None

# File overwrite behavior
AWS_S3_FILE_OVERWRITE = False

# Object parameters (e.g., caching)
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 day cache
}

# Authentication for URLs
AWS_QUERYSTRING_AUTH = True

# Storage classes
STATICFILES_STORAGE = 'erp_core.storage.CloudflareR2StaticStorage'
DEFAULT_FILE_STORAGE = 'erp_core.storage.CloudflareR2MediaStorage'

# URLs for static and media files
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/' if AWS_S3_CUSTOM_DOMAIN else f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{STATICFILES_LOCATION}/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/' if AWS_S3_CUSTOM_DOMAIN else f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{MEDIAFILES_LOCATION}/' 