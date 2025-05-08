# core/permissions.py
from rest_framework import permissions
from .models import UserRole


class IsAdminUser(permissions.BasePermission):
    """Allow access only to admin users"""
    
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == UserRole.ADMIN
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read-only access to any user, write access to admin only"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role == UserRole.ADMIN
        )


class IsSelfOrAdmin(permissions.BasePermission):
    """Allow users to edit their own data or admin to edit any"""
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == UserRole.ADMIN:
            return True
        
        return obj == request.user


class HasRolePermission(permissions.BasePermission):
    """Check if user's role has specific permission"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Map HTTP methods to permission types
        method_permissions = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        
        required_permission = method_permissions.get(request.method)
        if not required_permission:
            return False
        
        # Define permissions for each role and model
        role_permissions = {
            UserRole.ADMIN: ['view', 'create', 'update', 'delete'],
            UserRole.ENGINEER: ['view', 'create', 'update'],
            UserRole.OPERATOR: ['view', 'create'],
            UserRole.VIEWER: ['view'],
        }
        
        user_permissions = role_permissions.get(request.user.role, [])
        return required_permission in user_permissions