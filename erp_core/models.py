from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class ProductType(models.TextChoices):
    MONTAGED = 'MONTAGED', 'Montaged'
    SEMI = 'SEMI', 'Semi'
    SINGLE = 'SINGLE', 'Single'

class ComponentType(models.TextChoices):
    SEMI_PRODUCT = 'SEMI_PRODUCT', 'Semi Product'
    MANUFACTURING_PROCESS = 'MANUFACTURING_PROCESS', 'Manufacturing Process'
    RAW_MATERIAL = 'RAW_MATERIAL', 'Raw Material'

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

    def __str__(self):
        return self.username

class Customer(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code} - {self.name}"

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