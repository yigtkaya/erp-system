# common/models.py
from django.db import models
from django.db import transaction
from core.models import BaseModel
import uuid
import os

def get_file_extension(filename):
    """Get the file extension from filename"""
    return os.path.splitext(filename)[1]

class FileVersion(BaseModel):
    """Stores versions of files with complete history"""
    # File identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(max_length=100, help_text="Type of document (e.g., 'technical_drawing')")
    object_id = models.CharField(max_length=50, help_text="ID of the related object")
    version_number = models.PositiveIntegerField(help_text="Version number of this file")
    
    # File information
    file = models.FileField(upload_to='versioned_files/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=100, null=True, blank=True)
    
    # Version status
    is_current = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = [('content_type', 'object_id', 'version_number')]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['content_type', 'object_id', 'is_current']),
        ]
    
    def save(self, *args, **kwargs):
        """Override save to handle file metadata and versioning"""
        # Set file metadata if available
        if self.file and not self.file_size and hasattr(self.file, 'size'):
            self.file_size = self.file.size
            
            # Try to get content type if not set
            if not self.file_type and hasattr(self.file, 'content_type'):
                self.file_type = self.file.content_type

        # Ensure only one current version exists for this object
        if self.is_current:
            with transaction.atomic():
                FileVersion.objects.filter(
                    content_type=self.content_type,
                    object_id=self.object_id,
                    is_current=True
                ).exclude(pk=self.pk).update(is_current=False)
                
        super().save(*args, **kwargs)
    
    @property
    def file_url(self):
        """Get URL for the file"""
        if self.file:
            return self.file.url
        return None
        
    def __str__(self):
        return f"{self.content_type} - {self.object_id} (v{self.version_number})"
    
    @classmethod
    def get_current(cls, content_type, object_id):
        """Get the current version of a file"""
        return cls.objects.filter(
            content_type=content_type,
            object_id=object_id,
            is_current=True
        ).first()
    
    @classmethod
    def get_versions(cls, content_type, object_id):
        """Get all versions for an object"""
        return cls.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-version_number')

class FileManager:
    """Helper class for file operations"""
    
    @staticmethod
    def save_new_version(file, content_type, object_id, notes=None, created_by=None):
        """
        Save a new version of a file
        
        Args:
            file: Django file object
            content_type: Type of document
            object_id: ID of the related object
            notes: Optional notes about this version
            created_by: User who created this version
            
        Returns:
            FileVersion: The newly created file version
        """
        # Get the next version number
        latest = FileVersion.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-version_number').first()
        
        next_version = 1
        if latest:
            next_version = latest.version_number + 1
        
        # Create the new version
        version = FileVersion(
            content_type=content_type,
            object_id=object_id,
            version_number=next_version,
            file=file,
            original_filename=file.name,
            notes=notes,
            created_by=created_by
        )
        version.save()
        
        return version
    
    @staticmethod
    def set_current_version(version_id):
        """
        Set a specific version as current
        
        Args:
            version_id: UUID of the version to set as current
            
        Returns:
            FileVersion: The updated version
        """
        try:
            version = FileVersion.objects.get(pk=version_id)
            version.is_current = True
            version.save()  # This will automatically set others to not current
            return version
        except FileVersion.DoesNotExist:
            return None