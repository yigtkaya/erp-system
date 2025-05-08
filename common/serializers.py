# common/serializers.py
from rest_framework import serializers
from .models import FileVersion, AllowedFileType, FileCategory, ContentType
from core.serializers import UserSerializer
import os


class FileVersionSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    modified_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    size_readable = serializers.SerializerMethodField()
    
    class Meta:
        model = FileVersion
        fields = [
            'id', 'file_category', 'content_type', 'object_id', 
            'version_number', 'file', 'file_url', 'thumbnail_url', 
            'preview_url', 'original_filename', 'file_extension', 
            'mime_type', 'file_size', 'size_readable', 'is_current', 
            'notes', 'checksum', 'metadata', 'is_image', 'image_width', 
            'image_height', 'created_at', 'updated_at', 'created_by', 
            'modified_by'
        ]
        read_only_fields = [
            'id', 'file_url', 'thumbnail_url', 'preview_url', 
            'file_extension', 'mime_type', 'file_size', 'size_readable',
            'checksum', 'is_image', 'image_width', 'image_height',
            'created_at', 'updated_at', 'created_by', 'modified_by'
        ]
    
    def get_file_url(self, obj):
        return obj.file_url
    
    def get_thumbnail_url(self, obj):
        return obj.thumbnail_url
    
    def get_preview_url(self, obj):
        return obj.preview_url
    
    def get_size_readable(self, obj):
        if not obj.file_size:
            return "0B"
        
        import math
        size_bytes = obj.file_size
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"


class FileVersionUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    file_category = serializers.ChoiceField(choices=FileCategory.choices, required=False)
    content_type = serializers.ChoiceField(choices=ContentType.choices, required=True)
    object_id = serializers.CharField(max_length=50, required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
    
    def validate_file(self, value):
        # Check file extension
        ext = os.path.splitext(value.name)[1].lower()
        if not ext:
            raise serializers.ValidationError("File must have an extension")
        
        # Get file category from request data
        file_category = self.initial_data.get('file_category', FileCategory.OTHER)
        
        # Check if file type is allowed
        allowed = AllowedFileType.objects.filter(
            extension=ext,
            is_active=True,
            category=file_category
        ).first()
        
        if not allowed:
            raise serializers.ValidationError(
                f"File type {ext} is not allowed for category {file_category}"
            )
        
        # Check file size
        if value.size > allowed.max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(
                f"File size exceeds maximum allowed size of {allowed.max_size_mb}MB"
            )
        
        return value


class AllowedFileTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowedFileType
        fields = [
            'id', 'extension', 'mime_type', 'category', 
            'max_size_mb', 'is_active'
        ]
        read_only_fields = ['id']