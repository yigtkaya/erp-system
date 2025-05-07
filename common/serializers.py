# common/serializers.py
from rest_framework import serializers
from .models import FileVersion

class FileVersionSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FileVersion
        fields = [
            'id', 'content_type', 'object_id', 'version_number',
            'file', 'file_url', 'original_filename', 'file_size', 'file_type',
            'is_current', 'notes', 'created_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'version_number', 'file_url', 'file_size', 'file_type',
            'created_at', 'created_by_name'
        ]
    
    def get_file_url(self, obj):
        return obj.file_url
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None