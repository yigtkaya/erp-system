# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.exceptions import ValidationError
import re
from django.conf import settings
from .storage import get_temporary_file_url

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, username, password, **extra_fields)

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    ENGINEER = 'ENGINEER', 'Engineer'  
    OPERATOR = 'OPERATOR', 'Operator'
    VIEWER = 'VIEWER', 'Viewer'

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="%(app_label)s_%(class)s_created"
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="%(app_label)s_%(class)s_modified"
    )

    class Meta:
        abstract = True

class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.VIEWER)
    created_at = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return self.username

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'departments'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    employee_id = models.CharField(max_length=50, unique=True)
    is_department_head = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_profiles'
        ordering = ['employee_id']
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            # Generate employee ID
            last_profile = UserProfile.objects.order_by('-employee_id').first()
            if last_profile and last_profile.employee_id.startswith('EMP'):
                try:
                    last_num = int(last_profile.employee_id[3:])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
            self.employee_id = f'EMP{new_num:04d}'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.employee_id}"

class DepartmentMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='department_memberships')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='members')
    joined_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'department_memberships'
        unique_together = ['user', 'department']
    
    def __str__(self):
        return f"{self.user.username} in {self.department.name}"

class Customer(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'customers'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]
    
    def clean(self):
        # Validate customer code
        if not re.match(r'^[A-Za-z0-9\.]+$', self.code):
            raise ValidationError({
                'code': 'Customer code must contain only letters, numbers, and periods'
            })
        
        if len(self.code) < 4:
            raise ValidationError({
                'code': 'Customer code must be at least 4 characters'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class AuditLog(models.Model):
    table_name = models.CharField(max_length=100)
    record_id = models.IntegerField()
    action = models.CharField(max_length=10)  # CREATE, UPDATE, DELETE
    changed_data = models.JSONField()
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['changed_at']),
            models.Index(fields=['changed_by']),
        ]
    
    def __str__(self):
        return f"{self.action} on {self.table_name} [{self.record_id}] at {self.changed_at}"

class Permission(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'permissions'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class RolePermission(models.Model):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']
    
    def __str__(self):
        return f"{self.role} - {self.permission.name}"

class PrivateDocument(models.Model):
    """
    Example model for storing private documents that are not publicly accessible.
    These documents will require authentication to access.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    document = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        storage=settings.PRIVATE_FILE_STORAGE if hasattr(settings, 'PRIVATE_FILE_STORAGE') else None
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='private_documents',
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_document_url(self, expire_seconds=None):
        """
        Generate a temporary URL for accessing the document
        
        Args:
            expire_seconds: Number of seconds the URL will be valid
        
        Returns:
            Temporary URL with configured expiration
        """
        return get_temporary_file_url(self.document.name, expire_seconds=expire_seconds)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Private Document'
        verbose_name_plural = 'Private Documents'