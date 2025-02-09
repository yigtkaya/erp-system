from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.middleware.csrf import get_token
from guardian.shortcuts import assign_perm, get_objects_for_user
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings

from erp_core.models import User, UserProfile, Department, RolePermission
from erp_core.forms import UserRegistrationForm, UserProfileForm
from erp_core.permissions import IsAdminUser, HasDepartmentPermission

@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description="Session status",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'isAuthenticated': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'role': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                }
            )
        )
    },
    tags=['Authentication']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def check_session(request):
    if request.user.is_authenticated:
        return Response({
            'isAuthenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email,
                'role': request.user.role,
            }
        })
    return Response({'isAuthenticated': False})

@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
        }
    ),
    responses={
        200: openapi.Response(
            description="Successfully logged in",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'role': openapi.Schema(type=openapi.TYPE_STRING),
                        }
                    ),
                    'csrfToken': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: 'Invalid credentials'
    },
    tags=['Authentication']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'success': False,
            'message': 'Please provide both username and password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        if not user.is_active:
            return Response({
                'success': False,
                'message': 'This account is inactive'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Log the user in and create a session
        login(request, user)
        
        # Configure session
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)  # Use the session age from settings
        request.session['user_id'] = user.id
        request.session['role'] = user.role
        
        # Get CSRF token
        csrf_token = get_token(request)
        
        response = Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            },
            'csrfToken': csrf_token
        }, status=status.HTTP_200_OK)
        
        # Set session cookie settings
        response.set_cookie(
            settings.SESSION_COOKIE_NAME,
            request.session.session_key,
            max_age=settings.SESSION_COOKIE_AGE,
            domain=settings.SESSION_COOKIE_DOMAIN,
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=True,
            samesite=settings.SESSION_COOKIE_SAMESITE or 'Lax'
        )
        
        return response
    else:
        return Response({
            'success': False,
            'message': 'Invalid username or password'
        }, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='post',
    responses={
        200: openapi.Response(
            description="Successfully logged out",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        )
    },
    tags=['Authentication']
)
@api_view(['POST'])
@login_required
def logout_view(request):
    # Clear session data
    request.session.flush()
    logout(request)
    
    response = Response({
        'success': True,
        'message': 'Successfully logged out'
    }, status=status.HTTP_200_OK)
    
    # Clear session cookie
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        domain=settings.SESSION_COOKIE_DOMAIN,
        samesite=settings.SESSION_COOKIE_SAMESITE or 'Lax'
    )
    
    return response

class UserRegistrationView(UserPassesTestMixin, CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'erp_core/auth/register.html'
    success_url = reverse_lazy('user_list')

    @swagger_auto_schema(
        operation_description="Register a new user (Admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'email', 'password1', 'password2', 'role', 'department', 'employee_id'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email'),
                'password1': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
                'password2': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['ADMIN', 'MANAGER', 'STAFF']),
                'department': openapi.Schema(type=openapi.TYPE_INTEGER),
                'employee_id': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'role': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: 'Invalid input',
            403: 'Permission denied'
        },
        security=[{'Bearer': []}],
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'ADMIN'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password1'])
        user.save()
        
        # Create user profile
        UserProfile.objects.create(
            user=user,
            department_id=form.cleaned_data.get('department'),
            employee_id=form.cleaned_data.get('employee_id')
        )
        
        # Assign role-based permissions
        role_permissions = RolePermission.objects.filter(role=user.role)
        for role_perm in role_permissions:
            user.user_permissions.add(role_perm.permission)
        
        messages.success(self.request, f'Account created for {user.username}')
        return super().form_valid(form)

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'erp_core/auth/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'ADMIN'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(departments__in=self.request.user.departments.all())

class UserProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'erp_core/auth/profile.html'
    success_url = reverse_lazy('profile')

    @swagger_auto_schema(
        operation_description="Get or update user profile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'department': openapi.Schema(type=openapi.TYPE_INTEGER),
                'employee_id': openapi.Schema(type=openapi.TYPE_STRING),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'address': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(
                description="Profile retrieved/updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'department': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'employee_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                        'address': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            401: 'Authentication required',
            400: 'Invalid input'
        },
        security=[{'Bearer': []}],
        tags=['User Management']
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        return self.request.user.profile 