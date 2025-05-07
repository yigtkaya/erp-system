# erp_core/settings.py

INSTALLED_APPS = [
    # Other apps
    'storages',
    'core',
    'inventory',
    'manufacturing',
    'sales',
    'purchasing',
    'quality',
    'maintenance',
    'common',  # New app for shared functionality
]

# Cloudflare R2 Configuration
USE_CLOUDFLARE_R2 = True

if USE_CLOUDFLARE_R2:
    # R2 settings
    AWS_ACCESS_KEY_ID = 'your-r2-access-key'
    AWS_SECRET_ACCESS_KEY = 'your-r2-secret-key'
    AWS_STORAGE_BUCKET_NAME = 'your-erp-bucket'
    AWS_S3_ENDPOINT_URL = 'https://<account-id>.r2.cloudflarestorage.com'
    AWS_S3_REGION_NAME = 'auto'  # Cloudflare R2 uses 'auto'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.r2.dev'  # If you've set up custom domain
    
    # General S3 settings
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'private'  # Keep files private by default
    AWS_QUERYSTRING_AUTH = True  # Enable signed URLs for security
    AWS_S3_FILE_OVERWRITE = False  # Don't overwrite files with same name

    # Storage settings
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    # Optional: Media files URL
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
else:
    # Local storage fallback for development
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    MEDIA_URL = '/media/'