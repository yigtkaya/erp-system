from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class CloudflareR2Storage(S3Boto3Storage):
    """
    Custom storage class for Cloudflare R2.
    
    Cloudflare R2 is S3-compatible, so we can use the S3Boto3Storage class
    with custom endpoint_url and region_name.
    """
    access_key = settings.AWS_ACCESS_KEY_ID
    secret_key = settings.AWS_SECRET_ACCESS_KEY
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    endpoint_url = settings.AWS_S3_ENDPOINT_URL
    region_name = settings.AWS_S3_REGION_NAME
    custom_domain = settings.AWS_S3_CUSTOM_DOMAIN if hasattr(settings, 'AWS_S3_CUSTOM_DOMAIN') else None
    file_overwrite = settings.AWS_S3_FILE_OVERWRITE if hasattr(settings, 'AWS_S3_FILE_OVERWRITE') else True
    object_parameters = settings.AWS_S3_OBJECT_PARAMETERS if hasattr(settings, 'AWS_S3_OBJECT_PARAMETERS') else {}
    querystring_auth = settings.AWS_QUERYSTRING_AUTH if hasattr(settings, 'AWS_QUERYSTRING_AUTH') else True
    default_acl = settings.AWS_DEFAULT_ACL if hasattr(settings, 'AWS_DEFAULT_ACL') else None


class CloudflareR2StaticStorage(CloudflareR2Storage):
    """
    Storage for static files using Cloudflare R2.
    """
    location = settings.STATICFILES_LOCATION if hasattr(settings, 'STATICFILES_LOCATION') else 'static'


class CloudflareR2MediaStorage(CloudflareR2Storage):
    """
    Storage for media files using Cloudflare R2.
    """
    location = settings.MEDIAFILES_LOCATION if hasattr(settings, 'MEDIAFILES_LOCATION') else 'media' 