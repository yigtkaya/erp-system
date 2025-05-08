# common/permissions.py
from rest_framework import permissions
from core.models import UserRole


class CanManageFiles(permissions.BasePermission):
    """Permission class for file management"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions based on role
        if request.user.role in [UserRole.ADMIN, UserRole.ENGINEER]:
            return True
        
        # Operators can upload files but not delete
        if request.user.role == UserRole.OPERATOR and request.method != 'DELETE':
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin can do anything
        if request.user.role == UserRole.ADMIN:
            return True
        
        # Creator can modify their own files
        if obj.created_by == request.user:
            return True
        
        # Engineers can modify files
        if request.user.role == UserRole.ENGINEER:
            return True
        
        return False