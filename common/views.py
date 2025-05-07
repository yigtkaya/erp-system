# common/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import FileVersion, FileManager
from .serializers import FileVersionSerializer

class FileVersionViewSet(viewsets.ModelViewSet):
    queryset = FileVersion.objects.all()
    serializer_class = FileVersionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter file versions by query parameters"""
        queryset = FileVersion.objects.all().order_by('-created_at')
        
        content_type = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')
        current_only = self.request.query_params.get('current_only', 'false').lower() == 'true'
        
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        if object_id:
            queryset = queryset.filter(object_id=object_id)
        if current_only:
            queryset = queryset.filter(is_current=True)
            
        return queryset
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a new file version"""
        if 'file' not