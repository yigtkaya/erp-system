# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Department, UserProfile, Customer, AuditLog, Permission, RolePermission, PrivateDocument
from django.utils.safestring import mark_safe


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'email', 'created_at')
    search_fields = ('code', 'name', 'email')
    list_filter = ('created_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'record_id', 'action', 'changed_by', 'changed_at')
    list_filter = ('table_name', 'action', 'changed_at')
    search_fields = ('table_name', 'record_id')
    readonly_fields = ('table_name', 'record_id', 'action', 'changed_data', 'changed_by', 'changed_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PrivateDocument)
class PrivateDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at', 'document_url')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'document'),
        }),
        ('Document Access', {
            'fields': ('document_url',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def document_url(self, obj):
        """Display a temporary URL to the document in the admin"""
        if obj.document:
            url = obj.get_document_url(expire_seconds=3600)  # 1 hour expiration
            return mark_safe(f'<a href="{url}" target="_blank">Access document (URL expires in 1 hour)</a>')
        return "No document attached"
    document_url.short_description = "Document Access"


admin.site.register(User, UserAdmin)