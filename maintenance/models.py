# maintenance/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel, User
from manufacturing.models import WorkCenter
from common.models import FileVersionManager, ContentType


class MaintenanceType(models.TextChoices):
    PREVENTIVE = 'PREVENTIVE', 'Preventive'
    CORRECTIVE = 'CORRECTIVE', 'Corrective'
    PREDICTIVE = 'PREDICTIVE', 'Predictive'
    EMERGENCY = 'EMERGENCY', 'Emergency'


class MaintenanceStatus(models.TextChoices):
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    OVERDUE = 'OVERDUE', 'Overdue'


class MaintenancePriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical'


class Equipment(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE, related_name='equipment')
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    model_number = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    specifications = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'equipment'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class MaintenancePlan(BaseModel):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_plans')
    plan_name = models.CharField(max_length=100)
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices, default=MaintenanceType.PREVENTIVE)
    frequency_days = models.IntegerField()
    next_due_date = models.DateField()
    estimated_duration_hours = models.DecimalField(max_digits=5, decimal_places=2)
    instructions = models.TextField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'maintenance_plans'
        ordering = ['equipment', 'plan_name']
    
    def __str__(self):
        return f"{self.equipment.code} - {self.plan_name}"


class WorkOrder(BaseModel):
    work_order_number = models.CharField(max_length=50, unique=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_work_orders')
    maintenance_plan = models.ForeignKey(MaintenancePlan, on_delete=models.SET_NULL, null=True, blank=True)
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices)
    priority = models.CharField(max_length=20, choices=MaintenancePriority.choices, default=MaintenancePriority.MEDIUM)
    status = models.CharField(max_length=20, choices=MaintenanceStatus.choices, default=MaintenanceStatus.SCHEDULED)
    
    description = models.TextField()
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name='maintenance_work_orders')
    reported_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reported_maintenance_issues')
    
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'maintenance_work_orders'
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['work_order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_start']),
        ]
    
    def clean(self):
        if self.scheduled_end <= self.scheduled_start:
            raise ValidationError("Scheduled end must be after scheduled start")
    
    @property
    def is_overdue(self):
        if self.status not in [MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED]:
            return timezone.now() > self.scheduled_end
        return False
    
    def __str__(self):
        return f"{self.work_order_number} - {self.equipment.code}"
    
    # File management methods
    def upload_maintenance_report(self, file, notes=None, user=None):
        """Upload maintenance report"""
        return FileVersionManager.create_version(
            file=file,
            content_type=ContentType.MAINTENANCE_REPORT,
            object_id=str(self.id),
            notes=notes,
            user=user
        )


class MaintenanceTask(BaseModel):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='tasks')
    task_name = models.CharField(max_length=100)
    description = models.TextField()
    sequence_number = models.IntegerField()
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'maintenance_tasks'
        ordering = ['sequence_number']
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.task_name}"


class SparePart(BaseModel):
    part_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    equipment = models.ManyToManyField(Equipment, related_name='spare_parts')
    minimum_stock = models.IntegerField()
    current_stock = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey('purchasing.Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    
    class Meta:
        db_table = 'spare_parts'
        ordering = ['part_number']
    
    @property
    def is_below_minimum(self):
        return self.current_stock < self.minimum_stock
    
    def __str__(self):
        return f"{self.part_number} - {self.name}"


class MaintenancePartUsage(BaseModel):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='parts_used')
    spare_part = models.ForeignKey(SparePart, on_delete=models.PROTECT)
    quantity_used = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'maintenance_part_usage'
    
    @property
    def total_cost(self):
        return self.quantity_used * self.unit_cost
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.spare_part.part_number}"


class MaintenanceLog(BaseModel):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_logs')
    work_order = models.ForeignKey(WorkOrder, on_delete=models.SET_NULL, null=True, blank=True)
    log_type = models.CharField(max_length=50, choices=[
        ('BREAKDOWN', 'Breakdown'),
        ('MAINTENANCE', 'Maintenance'),
        ('INSPECTION', 'Inspection'),
        ('CALIBRATION', 'Calibration'),
        ('OTHER', 'Other'),
    ])
    description = models.TextField()
    action_taken = models.TextField()
    logged_by = models.ForeignKey(User, on_delete=models.PROTECT)
    log_date = models.DateTimeField(default=timezone.now)
    downtime_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'maintenance_logs'
        ordering = ['-log_date']
    
    def __str__(self):
        return f"{self.equipment.code} - {self.log_type} - {self.log_date}"