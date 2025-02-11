from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.core.exceptions import ValidationError

class ProductType(models.TextChoices):
    MONTAGED = 'MONTAGED', 'Montaged'
    SEMI = 'SEMI', 'Semi'
    SINGLE = 'SINGLE', 'Single'
    STANDARD_PART = 'STANDARD_PART', 'Standard Part'  # Added

class MaterialType(models.TextChoices):
    STEEL = 'STEEL', 'Steel'
    ALUMINUM = 'ALUMINUM', 'Aluminum'

class ComponentType(models.TextChoices):
    SEMI_PRODUCT = 'SEMI_PRODUCT', 'Semi Product'
    MONTAGED_PRODUCT = 'MONTAGED_PRODUCT', 'Montaged Product'
    RAW_MATERIAL = 'RAW_MATERIAL', 'Raw Material'
    STANDARD_PART = 'STANDARD_PART', 'Standard Part'  # Added
    
class MachineStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    IN_USE = 'IN_USE', 'In Use'
    MAINTENANCE = 'MAINTENANCE', 'Maintenance'
    RETIRED = 'RETIRED', 'Retired'

class WorkOrderStatus(models.TextChoices):
    PLANNED = 'PLANNED', 'Planned'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    DELAYED = 'DELAYED', 'Delayed'

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    ENGINEER = 'ENGINEER', 'Engineer'
    OPERATOR = 'OPERATOR', 'Operator'
    VIEWER = 'VIEWER', 'Viewer'

class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.VIEWER)
    last_login = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    departments = models.ManyToManyField('Department', blank=True, related_name='users')

    def __str__(self):
        return self.username

    def has_module_permission(self, app_label):
        if self.is_superuser:
            return True
        return self.role == UserRole.ADMIN or \
               self.user_permissions.filter(content_type__app_label=app_label).exists()

    def has_department_permission(self, department):
        return self.is_superuser or \
               self.departments.filter(id=department.id).exists() or \
               (self.profile.department == department and self.profile.is_department_head)

    def get_role_permissions(self):
        return Permission.objects.filter(
            Q(rolepermission__role=self.role) |
            Q(user=self)
        ).distinct()

class BaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="%(class)s_created", null=True, blank=True)
    modified_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="%(class)s_modified", null=True, blank=True)

    class Meta:
        abstract = True 

    def save(self, *args, **kwargs):
        if not self.pk:  # New instance
            self.created_at = timezone.now()
        self.modified_at = timezone.now()
        super().save(*args, **kwargs)

class Customer(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def clean(self):
        if not self.code.isalnum():
            raise ValidationError("Customer code must contain only letters and numbers")
        
        if len(self.code) < 4:
            raise ValidationError("Customer code must be at least 4 characters")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=50, unique=True)
    is_department_head = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class RolePermission(models.Model):
    role = models.CharField(max_length=20, choices=UserRole.choices)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['role', 'permission']
        
    def __str__(self):
        return f"{self.role} - {self.permission.codename}" 