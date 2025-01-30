from rest_framework import permissions
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == 'ADMIN'
        )

class HasDepartmentPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, 'department'):
            return True
        return request.user.has_department_permission(obj.department)

class DepartmentAccessMixin(UserPassesTestMixin):
    def test_func(self):
        if self.request.user.is_superuser:
            return True
        
        obj = self.get_object()
        if not hasattr(obj, 'department'):
            return True
            
        return self.request.user.has_department_permission(obj.department)

def department_access_required(view_func):
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
            
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        # Get the object based on the view's logic
        obj = view_func.get_object() if hasattr(view_func, 'get_object') else None
        
        if obj and hasattr(obj, 'department'):
            if not request.user.has_department_permission(obj.department):
                raise PermissionDenied
                
        return view_func(request, *args, **kwargs)
    return wrapped_view 