# core/views.py
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import User, Department, Customer, UserProfile, DepartmentMembership, AuditLog
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
    AuditLogSerializer
)
from .permissions import IsAdminOrReadOnly, IsSelfOrAdmin

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """Handle user registration"""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsAdminUser]  # Only admins can create users
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
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


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View audit logs"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['table_name', 'action', 'changed_by']
    search_fields = ['table_name', 'action']
    ordering = ['-changed_at']


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
        },
        'ENGINEER': {
            'users': ['view'],
            'products': ['view', 'create', 'update'],
            'customers': ['view', 'create', 'update'],
            'files': ['view', 'create', 'update'],
            'orders': ['view', 'create', 'update'],
            'reports': ['view', 'create'],
        },
        'OPERATOR': {
            'users': ['view'],
            'products': ['view', 'update'],
            'customers': ['view'],
            'files': ['view', 'create'],
            'orders': ['view', 'update'],
            'reports': ['view'],
        },
        'VIEWER': {
            'users': ['view'],
            'products': ['view'],
            'customers': ['view'],
            'files': ['view'],
            'orders': ['view'],
            'reports': ['view'],
        }
    }
    
    permissions['permissions'] = role_permissions.get(user.role, {})
    
    return Response(permissions)