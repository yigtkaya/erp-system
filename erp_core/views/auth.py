from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from guardian.shortcuts import assign_perm, get_objects_for_user
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from rest_framework.response import Response

from erp_core.models import User, UserProfile, Department, RolePermission
from erp_core.serializers import CustomTokenObtainPairSerializer
from erp_core.forms import UserRegistrationForm, UserProfileForm
from erp_core.permissions import IsAdminUser, HasDepartmentPermission

registration_schema = openapi.Schema(
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
)

class UserRegistrationView(UserPassesTestMixin, CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'erp_core/auth/register.html'
    success_url = reverse_lazy('user_list')

    @swagger_auto_schema(
        operation_description="Register a new user (Admin only)",
        request_body=registration_schema,
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

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="Successful login",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'role': openapi.Schema(type=openapi.TYPE_STRING),
                                'departments': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_INTEGER)
                                )
                            }
                        )
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            response.data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'departments': list(user.departments.values_list('id', flat=True))
            }
        return response

@swagger_auto_schema(
    method='post',
    operation_description="Logout the current user",
    responses={
        200: 'Successfully logged out',
        401: 'Authentication required'
    },
    security=[{'Bearer': []}],
    tags=['Authentication']
)
@api_view(['POST'])
@login_required
def logout_view(request):
    logout(request)
    return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK) 