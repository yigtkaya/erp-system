from django.db import models
from django.conf import settings

class PrivateDocument(models.Model):
    """
    Example model for storing private documents that are not publicly accessible.
    These documents will require authentication to access.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    document = models.FileField(
        upload_to='documents/%Y/%m/%d/'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='private_documents',
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_document_url(self, expire_seconds=None):
        """
        Generate a temporary URL for accessing the document
        
        Args:
            expire_seconds: Number of seconds the URL will be valid
        
        Returns:
            Temporary URL with configured expiration
        """
        from core.storage import get_temporary_file_url
        return get_temporary_file_url(self.document.name, expire_seconds=expire_seconds) 