from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction, connection
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import User, Department, Customer, UserProfile, DepartmentMembership, AuditLog, PrivateDocument
from .serializers import (
    UserSerializer, 
    UserCreateSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    DepartmentSerializer,
    CustomerSerializer,
    UserProfileSerializer,
    LoginSerializer,
    UserListSerializer,
    AuditLogSerializer,
    PrivateDocumentSerializer
)
from .permissions import IsAdminOrReadOnly, IsSelfOrAdmin, HasRolePermission
from .exports import ExportService
from .imports import ImportService
from .dashboard import DashboardService
from .emails import EmailService
import time
import psutil
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema(
    tags=['auth'],
    description='Register a new user',
    responses={201: UserSerializer}
)
class UserRegistrationView(generics.CreateAPIView):
    """Handle user registration"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsAdminUser]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
            # Send welcome email
            EmailService.send_user_welcome_email(user)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            # Create audit log
            AuditLog.objects.create(
                table_name='users',
                record_id=user.id,
                action='CREATE',
                changed_data={
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                },
                changed_by=request.user
            )
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['auth'],
    description='Login to get JWT tokens',
    responses={200: {'type': 'object', 'properties': {
        'user': {'$ref': '#/components/schemas/User'},
        'tokens': {'type': 'object', 'properties': {
            'refresh': {'type': 'string'},
            'access': {'type': 'string'}
        }}
    }}}
)
class LoginView(generics.GenericAPIView):
    """Handle user login"""
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=email, password=password)
        
        if user and user.is_active:
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            })
        else:
            return Response(
                {'error': 'Invalid credentials or inactive account'},
                status=status.HTTP_401_UNAUTHORIZED
            )


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint for monitoring"""
    health_status = {
        'status': 'healthy',
        'timestamp': time.time(),
        'services': {}
    }
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status['services']['cache'] = 'healthy'
        else:
            health_status['services']['cache'] = 'unhealthy'
            health_status['status'] = 'unhealthy'
    except Exception:
        health_status['services']['cache'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
    
    # Check file storage
    try:
        from django.core.files.storage import default_storage
        default_storage.exists('test')
        health_status['services']['storage'] = 'healthy'
    except Exception:
        health_status['services']['storage'] = 'unhealthy'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return Response(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint with available endpoints"""
    return Response({
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'login': '/api/auth/token/',
                'refresh': '/api/auth/token/refresh/',
                'verify': '/api/auth/token/verify/',
                'register': '/api/auth/register/',
                'logout': '/api/auth/logout/',
                'permissions': '/api/auth/permissions/',
            },
            'users': '/api/users/',
            'inventory': '/api/inventory/',
            'manufacturing': '/api/manufacturing/',
            'sales': '/api/sales/',
            'purchasing': '/api/purchasing/',
            'quality': '/api/quality/',
            'maintenance': '/api/maintenance/',
            'files': '/api/files/',
            'dashboard': '/api/dashboard/',
        },
        'documentation': {
            'swagger': '/api/docs/',
            'redoc': '/api/redoc/',
            'schema': '/api/schema/',
        },
        'health': '/health/',
        'metrics': '/api/metrics/',
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Handle user logout by blacklisting the refresh token"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'status': 'Successfully logged out'})
        else:
            return Response(
                {'error': 'Refresh token required'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except TokenError as e:
        return Response(
            {'error': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_permissions(request):
    """Get current user's permissions based on role"""
    user = request.user
    
    permissions = {
        'role': user.role,
        'is_active': user.is_active,
        'is_admin': user.role == 'ADMIN',
        'permissions': {}
    }
    
    # Define permissions based on role
    role_permissions = {
        'ADMIN': {
            'users': ['view', 'create', 'update', 'delete'],
            'products': ['view', 'create', 'update', 'delete'],
            'customers': ['view', 'create', 'update', 'delete'],
            'files': ['view', 'create', 'update', 'delete'],
            'orders': ['view', 'create', 'update', 'delete', 'approve'],
            'reports': ['view', 'create', 'export'],
            'dashboard': ['view', 'export'],
        },
        'ENGINEER': {
            'users': ['view'],
            'products': ['view', 'create', 'update'],
            'customers': ['view', 'create', 'update'],
            'files': ['view', 'create', 'update'],
            'orders': ['view', 'create', 'update'],
            'reports': ['view', 'create'],
            'dashboard': ['view'],
        },
        'OPERATOR': {
            'users': ['view'],
            'products': ['view', 'update'],
            'customers': ['view'],
            'files': ['view', 'create'],
            'orders': ['view', 'update'],
            'reports': ['view'],
            'dashboard': ['view'],
        },
        'VIEWER': {
            'users': ['view'],
            'products': ['view'],
            'customers': ['view'],
            'files': ['view'],
            'orders': ['view'],
            'reports': ['view'],
            'dashboard': ['view'],
        }
    }
    
    permissions['permissions'] = role_permissions.get(user.role, {})
    
    return Response(permissions)


@extend_schema(
    tags=['dashboard'],
    description='Get comprehensive dashboard overview data',
    parameters=[
        OpenApiParameter(
            name='period', 
            description='Time period for metrics (daily, weekly, monthly, yearly)',
            required=False, 
            type=OpenApiTypes.STR,
            default='monthly'
        ),
        OpenApiParameter(
            name='date', 
            description='Reference date in YYYY-MM-DD format (defaults to today)',
            required=False, 
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name='modules', 
            description='Comma-separated list of modules to include (inventory,sales,production,quality,maintenance,purchasing)',
            required=False, 
            type=OpenApiTypes.STR
        ),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'inventory': {'type': 'object'},
                'sales': {'type': 'object'},
                'production': {'type': 'object'},
                'quality': {'type': 'object'},
                'maintenance': {'type': 'object'},
                'purchasing': {'type': 'object'},
                'trends': {'type': 'object'},
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    """Get comprehensive dashboard overview data"""
    # Parse query parameters
    period = request.query_params.get('period', 'monthly')
    date_str = request.query_params.get('date')
    modules_str = request.query_params.get('modules')
    
    # Parse reference date
    if date_str:
        try:
            reference_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        reference_date = timezone.now().date()
    
    # Parse modules to include
    if modules_str:
        modules_to_include = modules_str.split(',')
    else:
        modules_to_include = ['inventory', 'sales', 'production', 'quality', 'maintenance', 'purchasing', 'trends']
    
    # Generate cache key based on parameters
    cache_key = f"dashboard:{period}:{reference_date}:{','.join(modules_to_include)}:{request.user.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    try:
        # Get all dashboard data
        all_stats = DashboardService.get_overview_stats(
            reference_date=reference_date,
            period=period
        )
        
        # Filter to only requested modules
        filtered_stats = {k: v for k, v in all_stats.items() if k in modules_to_include}
        
        # Cache the result (5 minute TTL)
        cache.set(cache_key, filtered_stats, timeout=300)
        
        return Response(filtered_stats)
    except Exception as e:
        logger.exception("Dashboard data error")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['dashboard'],
    description='Get dashboard data for a specific module',
    parameters=[
        OpenApiParameter(
            name='module', 
            description='Module name (inventory, sales, production, quality, maintenance, purchasing, trends)',
            required=True, 
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name='period', 
            description='Time period for metrics (daily, weekly, monthly, yearly)',
            required=False, 
            type=OpenApiTypes.STR,
            default='monthly'
        ),
        OpenApiParameter(
            name='date', 
            description='Reference date in YYYY-MM-DD format (defaults to today)',
            required=False, 
            type=OpenApiTypes.DATE
        ),
    ],
    responses={
        200: {'type': 'object'},
        400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
        404: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_module(request, module):
    """Get dashboard data for a specific module"""
    valid_modules = ['inventory', 'sales', 'production', 'quality', 'maintenance', 'purchasing', 'trends']
    
    if module not in valid_modules:
        return Response(
            {'error': f'Invalid module. Choose from: {", ".join(valid_modules)}'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Parse query parameters
    period = request.query_params.get('period', 'monthly')
    date_str = request.query_params.get('date')
    
    # Parse reference date
    if date_str:
        try:
            reference_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    else:
        reference_date = timezone.now().date()
    
    # Generate cache key
    cache_key = f"dashboard:module:{module}:{period}:{reference_date}:{request.user.id}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    try:
        # Get module-specific data
        module_data = DashboardService.get_module_stats(
            module=module,
            reference_date=reference_date,
            period=period
        )
        
        # Add metadata
        module_data['metadata'] = {
            'module': module,
            'period': period,
            'reference_date': reference_date.isoformat(),
            'generated_at': timezone.now().isoformat(),
        }
        
        # Cache the result (5 minute TTL)
        cache.set(cache_key, module_data, timeout=300)
        
        return Response(module_data)
    except Exception as e:
        logger.exception(f"Dashboard module data error: {module}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_metrics(request):
    """Get system metrics for monitoring"""
    return Response({
        'cpu_percent': psutil.cpu_percent(),
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent,
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'used': psutil.disk_usage('/').used,
            'free': psutil.disk_usage('/').free,
            'percent': psutil.disk_usage('/').percent,
        },
        'timestamp': datetime.now().isoformat()
    })


@extend_schema(tags=['users'])
class UserViewSet(viewsets.ModelViewSet):
    """User management viewset"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'is_active', 'department_memberships__department']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            permission_classes = [IsAdminUser]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsSelfOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's information"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password"""
        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Check if admin is changing another user's password
            if request.user.role == 'ADMIN' and user != request.user:
                # Admin can change any password without old password
                user.set_password(serializer.validated_data['new_password'])
                user.save()
            else:
                # Users must provide old password to change their own
                if not user.check_password(serializer.validated_data['old_password']):
                    return Response(
                        {'old_password': 'Wrong password.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                user.set_password(serializer.validated_data['new_password'])
                user.save()
            
            # Create audit log
            AuditLog.objects.create(
                table_name='users',
                record_id=user.id,
                action='UPDATE',
                changed_data={'password': 'changed'},
                changed_by=request.user
            )
            
            return Response({'status': 'Password changed successfully'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        """Activate/deactivate user"""
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can change user status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        is_active = request.data.get('is_active', True)
        
        if user == request.user and not is_active:
            return Response(
                {'error': 'You cannot deactivate yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = is_active
        user.save()
        
        # Create audit log
        AuditLog.objects.create(
            table_name='users',
            record_id=user.id,
            action='UPDATE',
            changed_data={'is_active': is_active},
            changed_by=request.user
        )
        
        status_text = 'activated' if is_active else 'deactivated'
        return Response({'status': f'User {status_text} successfully'})
    
    @action(detail=True, methods=['post'])
    def assign_departments(self, request, pk=None):
        """Assign user to departments"""
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only admins can manage department assignments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        department_ids = request.data.get('department_ids', [])
        
        with transaction.atomic():
            # Remove existing department memberships
            DepartmentMembership.objects.filter(user=user).delete()
            
            # Create new memberships
            for dept_id in department_ids:
                try:
                    department = Department.objects.get(id=dept_id)
                    DepartmentMembership.objects.create(
                        user=user,
                        department=department
                    )
                except Department.DoesNotExist:
                    continue
            
            # Update user's primary department if specified
            primary_dept_id = request.data.get('primary_department_id')
            if primary_dept_id:
                try:
                    primary_dept = Department.objects.get(id=primary_dept_id)
                    if hasattr(user, 'profile'):
                        user.profile.department = primary_dept
                        user.profile.save()
                except Department.DoesNotExist:
                    pass
        
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export users to Excel/CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
        headers = ['Username', 'Email', 'First Name', 'Last Name', 'Role', 'Active', 'Created At']
        
        format_type = request.query_params.get('format', 'excel')
        
        if format_type == 'csv':
            return ExportService.export_to_csv(queryset, 'users.csv', fields, headers)
        else:
            return ExportService.export_to_excel(queryset, 'users.xlsx', fields, headers)


@extend_schema(tags=['departments'])
class DepartmentViewSet(viewsets.ModelViewSet):
    """Department management viewset"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members of a department"""
        department = self.get_object()
        memberships = DepartmentMembership.objects.filter(department=department)
        users = [m.user for m in memberships]
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)


@extend_schema(tags=['customers'])
class CustomerViewSet(viewsets.ModelViewSet):
    """Customer management viewset"""
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['code', 'name']
    search_fields = ['code', 'name', 'email']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['code']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export customers to Excel/CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        
        fields = ['code', 'name', 'email', 'phone', 'address', 'created_at']
        headers = ['Code', 'Name', 'Email', 'Phone', 'Address', 'Created At']
        
        format_type = request.query_params.get('format', 'excel')
        
        if format_type == 'csv':
            return ExportService.export_to_csv(queryset, 'customers.csv', fields, headers)
        else:
            return ExportService.export_to_excel(queryset, 'customers.xlsx', fields, headers)
    
    @action(detail=False, methods=['post'])
    def import_data(self, request):
        """Import customers from Excel"""
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        field_mapping = {
            'Code': 'code',
            'Name': 'name',
            'Email': 'email',
            'Phone': 'phone',
            'Address': 'address',
        }
        
        try:
            results = ImportService.import_from_excel(
                file, Customer, field_mapping, request.user
            )
            return Response(results)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


@extend_schema(tags=['audit'])
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View audit logs"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['table_name', 'action', 'changed_by']
    search_fields = ['table_name', 'action']
    ordering = ['-changed_at']


class PrivateDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for private documents
    
    These documents are stored in Cloudflare R2 with private ACL.
    Temporary URLs are generated for access with configurable expiration.
    """
    queryset = PrivateDocument.objects.all()
    serializer_class = PrivateDocumentSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['created_at']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Add the current user as the creator of the document"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def extended_access(self, request, pk=None):
        """
        Generate a URL with extended access time (1 hour)
        """
        document = self.get_object()
        serializer = self.get_serializer(
            document, 
            context={'expire_seconds': 3600}  # 1 hour
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def short_access(self, request, pk=None):
        """
        Generate a URL with short access time (1 minute)
        """
        document = self.get_object()
        serializer = self.get_serializer(
            document, 
            context={'expire_seconds': 60}  # 1 minute
        )
        return Response(serializer.data)


@extend_schema(tags=['users'])
class UserProfileViewSet(viewsets.ModelViewSet):
    """User profile management viewset"""
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsSelfOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)