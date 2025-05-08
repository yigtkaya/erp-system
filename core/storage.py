# core/storage.py
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from django.utils.module_loading import import_string
import time


class CloudflareR2Storage(S3Boto3Storage):
    """
    Custom storage class for Cloudflare R2.
    This provides more control and clarity over the storage behavior.
    """
    location = 'media'  # The folder inside the bucket where files will be stored
    file_overwrite = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any custom initialization here if needed


class StaticCloudflareR2Storage(S3Boto3Storage):
    """
    Storage for static files in Cloudflare R2.
    Only used if you want to store static files in R2 instead of using default static files storage.
    """
    location = 'static'
    file_overwrite = True


class PrivateCloudflareR2Storage(S3Boto3Storage):
    """
    Storage for private files in Cloudflare R2.
    Use this for files that should not be publicly accessible.
    """
    location = 'private'
    file_overwrite = False
    default_acl = 'private'
    custom_domain = None  # Don't use custom domain for private files
    querystring_auth = True  # Use querystring authentication
    querystring_expire = 300  # URL expiration time in seconds (5 minutes)


def get_temporary_file_url(file_field, expire_seconds=None):
    """
    Generate a temporary URL for a private file.
    
    Args:
        file_field: A FileField or ImageField instance that is stored in a private storage
        expire_seconds: How long the URL should be valid for (defaults to storage setting)
        
    Returns:
        Temporary URL with time-limited access to the file
    """
    if not file_field:
        return None
    
    # Get the storage class
    storage = file_field.storage
    
    # If it's a string, import it
    if isinstance(storage, str):
        storage = import_string(storage)()
    
    # Check if this is a private storage with querystring auth
    if not getattr(storage, 'querystring_auth', False):
        # If not private, just return the regular URL
        return file_field.url
    
    # Generate temporary URL
    params = {}
    if expire_seconds:
        params['expire'] = int(time.time() + expire_seconds)
    
    return storage.url(file_field.name, **params) 