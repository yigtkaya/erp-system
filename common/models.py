# common/models.py
from django.db import models
from django.db import transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from core.models import BaseModel
import os
import uuid
import hashlib
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFit


def generate_file_path(instance, filename):
    """Generate a unique path for each file in R2"""
    ext = os.path.splitext(filename)[1]
    uuid_name = uuid.uuid4().hex
    
    # Organize files by type and date
    date_path = instance.created_at.strftime('%Y/%m/%d')
    base_path = f"files/{instance.file_category}/{instance.content_type}"
    
    return f"{base_path}/{date_path}/{uuid_name}{ext}"


class FileCategory(models.TextChoices):
    TECHNICAL = 'TECHNICAL', 'Technical Documents'
    QUALITY = 'QUALITY', 'Quality Documents'
    ORDER = 'ORDER', 'Order Documents'
    PRODUCT = 'PRODUCT', 'Product Images'
    MANUAL = 'MANUAL', 'Manuals'
    REPORT = 'REPORT', 'Reports'
    OTHER = 'OTHER', 'Other'


class ContentType(models.TextChoices):
    TECHNICAL_DRAWING = 'technical_drawing', 'Technical Drawing'
    PRODUCT_IMAGE = 'product_image', 'Product Image'
    QUALITY_DOCUMENT = 'quality_document', 'Quality Document'
    QUALITY_IMAGE = 'quality_image', 'Quality Image'
    PURCHASE_ORDER = 'purchase_order', 'Purchase Order'
    SALES_ORDER = 'sales_order', 'Sales Order'
    WORK_ORDER = 'work_order', 'Work Order'
    MAINTENANCE_REPORT = 'maintenance_report', 'Maintenance Report'
    USER_MANUAL = 'user_manual', 'User Manual'
    CERTIFICATE = 'certificate', 'Certificate'
    INVOICE = 'invoice', 'Invoice'
    OTHER = 'other', 'Other'


class AllowedFileType(models.Model):
    extension = models.CharField(max_length=10, unique=True)
    mime_type = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=FileCategory.choices)
    max_size_mb = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'allowed_file_types'
        ordering = ['extension']
    
    def __str__(self):
        return f"{self.extension} ({self.mime_type})"


class FileVersion(BaseModel):
    """Stores versions of files with their metadata in R2"""
    file_category = models.CharField(max_length=20, choices=FileCategory.choices)
    content_type = models.CharField(max_length=50, choices=ContentType.choices)
    object_id = models.CharField(max_length=50, help_text="ID of the related object")
    version_number = models.PositiveIntegerField(help_text="Version number of this file")
    file = models.FileField(
        upload_to=generate_file_path, 
        storage=settings.PRIVATE_FILE_STORAGE if settings.USE_CLOUDFLARE_R2 else None
    )
    original_filename = models.CharField(max_length=255, help_text="Original filename")
    file_extension = models.CharField(max_length=10)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    file_size = models.PositiveBigIntegerField(help_text="File size in bytes")
    is_current = models.BooleanField(default=True, help_text="Whether this is the current version")
    notes = models.TextField(blank=True, null=True, help_text="Notes about this version")
    checksum = models.CharField(max_length=64, help_text="SHA256 checksum for integrity verification")
    metadata = models.JSONField(blank=True, null=True, help_text="Additional metadata")
    
    # Image specific fields
    is_image = models.BooleanField(default=False)
    image_width = models.PositiveIntegerField(blank=True, null=True)
    image_height = models.PositiveIntegerField(blank=True, null=True)
    
    # Thumbnails for images (generated and stored in R2)
    thumbnail = ImageSpecField(
        source='file',
        processors=[ResizeToFit(300, 300)],
        format='JPEG',
        options={'quality': 80}
    )
    
    preview = ImageSpecField(
        source='file',
        processors=[ResizeToFit(800, 800)],
        format='JPEG',
        options={'quality': 90}
    )
    
    class Meta:
        db_table = 'file_versions'
        unique_together = [('content_type', 'object_id', 'version_number')]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['content_type', 'object_id', 'is_current']),
            models.Index(fields=['file_category']),
            models.Index(fields=['created_at']),
            models.Index(fields=['checksum']),
        ]
        ordering = ['-version_number']
    
    def clean(self):
        # Validate file type
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()
            if not ext:
                raise ValidationError({'file': 'File must have an extension'})
            
            allowed_type = AllowedFileType.objects.filter(
                extension=ext, 
                is_active=True,
                category=self.file_category
            ).first()
            
            if not allowed_type:
                raise ValidationError({
                    'file': f'File type {ext} is not allowed for category {self.file_category}'
                })
            
            # Check file size
            if self.file.size > allowed_type.max_size_mb * 1024 * 1024:
                raise ValidationError({
                    'file': f'File size exceeds maximum allowed size of {allowed_type.max_size_mb}MB'
                })
    
    def save(self, *args, **kwargs):
        # Set file metadata
        if self.file and not self.file_size:
            self.file_size = self.file.size
        
        if self.file and not self.file_extension:
            self.file_extension = os.path.splitext(self.file.name)[1].lower()
        
        if self.file and not self.mime_type and hasattr(self.file, 'content_type'):
            self.mime_type = self.file.content_type
        
        # Check if file is an image
        if self.mime_type and self.mime_type.startswith('image/'):
            self.is_image = True
            # You can add image dimension extraction here if needed
        
        # Generate checksum if not present
        if self.file and not self.checksum:
            self.checksum = self._generate_checksum()
        
        # Ensure only one current version per file
        if self.is_current:
            with transaction.atomic():
                FileVersion.objects.filter(
                    content_type=self.content_type,
                    object_id=self.object_id,
                    is_current=True
                ).exclude(pk=self.pk).update(is_current=False)
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def _generate_checksum(self):
        """Generate SHA256 checksum for the file"""
        hasher = hashlib.sha256()
        if self.file:
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.file.seek(0)  # Reset file pointer
        return hasher.hexdigest()
    
    @property
    def file_url(self):
        """Get the R2 URL for the file"""
        if self.file:
            return self.file.url
        return None
    
    @property
    def thumbnail_url(self):
        """Get the R2 URL for the thumbnail if it's an image"""
        if self.is_image and self.thumbnail:
            return self.thumbnail.url
        return None
    
    @property
    def preview_url(self):
        """Get the R2 URL for the preview if it's an image"""
        if self.is_image and self.preview:
            return self.preview.url
        return None
    
    def __str__(self):
        return f"{self.content_type} - {self.object_id} (v{self.version_number})"


class FileVersionManager:
    """Manager class for handling file versions"""
    
    @staticmethod
    def create_version(file, content_type, object_id, file_category=None, notes=None, 
                      metadata=None, user=None):
        """Create a new version of a file"""
        with transaction.atomic():
            # Get the latest version number
            latest = FileVersion.objects.filter(
                content_type=content_type,
                object_id=object_id
            ).order_by('-version_number').first()
            
            version_number = 1
            if latest:
                version_number = latest.version_number + 1
            
            # Auto-detect file category if not provided
            if not file_category:
                if content_type == ContentType.TECHNICAL_DRAWING:
                    file_category = FileCategory.TECHNICAL
                elif content_type == ContentType.QUALITY_DOCUMENT:
                    file_category = FileCategory.QUALITY
                elif content_type in [ContentType.PURCHASE_ORDER, ContentType.SALES_ORDER]:
                    file_category = FileCategory.ORDER
                else:
                    file_category = FileCategory.OTHER
            
            # Create new version
            version = FileVersion(
                file_category=file_category,
                content_type=content_type,
                object_id=object_id,
                version_number=version_number,
                file=file,
                original_filename=file.name,
                notes=notes,
                metadata=metadata,
                is_current=True,
                created_by=user
            )
            version.save()
            
            return version
    
    @staticmethod
    def get_current(content_type, object_id):
        """Get the current version of a file"""
        return FileVersion.objects.filter(
            content_type=content_type,
            object_id=object_id,
            is_current=True
        ).first()
    
    @staticmethod
    def get_all_versions(content_type, object_id):
        """Get all versions of a file"""
        return FileVersion.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-version_number')
    
    @staticmethod
    def set_as_current(version_id):
        """Set a specific version as the current one"""
        with transaction.atomic():
            version = FileVersion.objects.get(pk=version_id)
            
            # Set all other versions to not current
            FileVersion.objects.filter(
                content_type=version.content_type,
                object_id=version.object_id,
                is_current=True
            ).update(is_current=False)
            
            # Set this version as current
            version.is_current = True
            version.save()
            
            return version
    
    @staticmethod
    def delete_version(version_id):
        """Delete a specific version (cannot delete current version)"""
        version = FileVersion.objects.get(pk=version_id)
        
        if version.is_current:
            raise ValidationError("Cannot delete the current version")
        
        # Delete the file from R2
        if version.file:
            version.file.delete(save=False)
        
        # Delete the database record
        version.delete()
    
    @staticmethod
    def get_storage_stats(content_type=None, file_category=None):
        """Get storage statistics"""
        queryset = FileVersion.objects.all()
        
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        if file_category:
            queryset = queryset.filter(file_category=file_category)
        
        total_size = queryset.aggregate(
            total=models.Sum('file_size')
        )['total'] or 0
        
        total_files = queryset.count()
        current_files = queryset.filter(is_current=True).count()
        
        return {
            'total_files': total_files,
            'current_files': current_files,
            'total_size': total_size,
            'total_versions': total_files - current_files,
            'average_file_size': total_size / total_files if total_files > 0 else 0,
       }