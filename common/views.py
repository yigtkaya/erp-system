# common/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q
from .models import FileVersion, FileVersionManager, AllowedFileType
from .serializers import FileVersionSerializer, AllowedFileTypeSerializer
from .permissions import CanManageFiles


class FileVersionViewSet(viewsets.ModelViewSet):
    queryset = FileVersion.objects.all()
    serializer_class = FileVersionSerializer
    permission_classes = [IsAuthenticated, CanManageFiles]
    parser_classes = (MultiPartParser, FormParser)
    filterset_fields = ['file_category', 'content_type', 'object_id', 'is_current']
    search_fields = ['original_filename', 'notes']
    ordering_fields = ['created_at', 'version_number', 'file_size']
    ordering = ['-version_number']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by query parameters
        content_type = self.request.query_params.get('content_type')
        object_id = self.request.query_params.get('object_id')
        file_category = self.request.query_params.get('file_category')
        current_only = self.request.query_params.get('current_only', 'false').lower() == 'true'
        
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        if object_id:
            queryset = queryset.filter(object_id=object_id)
        
        if file_category:
            queryset = queryset.filter(file_category=file_category)
        
        if current_only:
            queryset = queryset.filter(is_current=True)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a new file version to R2"""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        content_type = request.data.get('content_type')
        object_id = request.data.get('object_id')
        file_category = request.data.get('file_category')
        notes = request.data.get('notes')
        metadata = request.data.get('metadata')
        
        if not content_type or not object_id:
            return Response(
                {'error': 'content_type and object_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Parse metadata if it's a string
            if metadata and isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except json.JSONDecodeError:
                    metadata = None
            
            # Create new version
            version = FileVersionManager.create_version(
                file=file,
                content_type=content_type,
                object_id=object_id,
                file_category=file_category,
                notes=notes,
                metadata=metadata,
                user=request.user
            )
            
            serializer = self.get_serializer(version)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def set_as_current(self, request, pk=None):
        """Set a version as the current one"""
        try:
            version = FileVersionManager.set_as_current(pk)
            serializer = self.get_serializer(version)
            return Response(serializer.data)
        except FileVersion.DoesNotExist:
            return Response(
                {'error': 'Version not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'])
    def delete_version(self, request, pk=None):
        """Delete a specific version"""
        try:
            FileVersionManager.delete_version(pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FileVersion.DoesNotExist:
            return Response(
                {'error': 'Version not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Get download information for a file"""
        version = self.get_object()
        
        if version.file:
            return Response({
                'url': version.file_url,
                'filename': version.original_filename,
                'size': version.file_size,
                'mime_type': version.mime_type,
                'checksum': version.checksum
            })
        
        return Response(
            {'error': 'File not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['get'])
    def storage_stats(self, request):
        """Get storage statistics"""
        content_type = request.query_params.get('content_type')
        file_category = request.query_params.get('file_category')
        
        stats = FileVersionManager.get_storage_stats(
            content_type=content_type,
            file_category=file_category
        )
        
        # Add human-readable size
        stats['total_size_readable'] = self._human_readable_size(stats['total_size'])
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def validate_file(self, request):
        """Validate a file before upload"""
        filename = request.query_params.get('filename')
        file_size = request.query_params.get('file_size')
        file_category = request.query_params.get('file_category')
        
        if not filename:
            return Response(
                {'error': 'filename is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ext = os.path.splitext(filename)[1].lower()
        
        allowed_type = AllowedFileType.objects.filter(
            extension=ext,
            is_active=True,
            category=file_category if file_category else FileCategory.OTHER
        ).first()
        
        if not allowed_type:
            return Response({
                'valid': False,
                'error': f'File type {ext} is not allowed for this category'
            })
        
        if file_size:
            try:
                size = int(file_size)
                max_size = allowed_type.max_size_mb * 1024 * 1024
                if size > max_size:
                    return Response({
                        'valid': False,
                        'error': f'File size exceeds maximum allowed size of {allowed_type.max_size_mb}MB'
                    })
            except ValueError:
                pass
        
        return Response({
            'valid': True,
            'mime_type': allowed_type.mime_type,
            'max_size_mb': allowed_type.max_size_mb
        })
    
    def _human_readable_size(self, size_bytes):
        """Convert bytes to human readable format"""
        if size_bytes == 0:
            return "0B"
        
        import math
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"


class AllowedFileTypeViewSet(viewsets.ModelViewSet):
    queryset = AllowedFileType.objects.all()
    serializer_class = AllowedFileTypeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category', 'is_active']
    search_fields = ['extension', 'mime_type']
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get allowed file types grouped by category"""
        file_types = AllowedFileType.objects.filter(is_active=True)
        
        grouped = {}
        for category, label in FileCategory.choices:
            category_types = file_types.filter(category=category)
            grouped[category] = {
                'label': label,
                'types': AllowedFileTypeSerializer(category_types, many=True).data
            }
        
        return Response(grouped)