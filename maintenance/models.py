# maintenance/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel
from manufacturing.models import ControlGauge, Fixture
from common.models import FileVersionManager, ContentType
import datetime


class EquipmentStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    INACTIVE = 'INACTIVE', 'Inactive'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    REPAIR = 'REPAIR', 'Under Repair'
    DISPOSED = 'DISPOSED', 'Disposed'


class MaintenanceType(models.TextChoices):
    PREVENTIVE = 'PREVENTIVE', 'Preventive'
    CORRECTIVE = 'CORRECTIVE', 'Corrective'
    PREDICTIVE = 'PREDICTIVE', 'Predictive'
    BREAKDOWN = 'BREAKDOWN', 'Breakdown'
    SAFETY = 'SAFETY', 'Safety'


class MaintenanceStatus(models.TextChoices):
    PLANNED = 'PLANNED', 'Planned'
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    ON_HOLD = 'ON_HOLD', 'On Hold'


class MaintenancePriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical'


class Equipment(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=EquipmentStatus.choices, default=EquipmentStatus.ACTIVE)
    location = models.CharField(max_length=100, blank=True, null=True)
    parent_equipment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_equipment')
    
    # Maintenance scheduling fields
    maintenance_interval_days = models.IntegerField(default=90, help_text="Maintenance interval in days")
    last_maintenance_date = models.DateField(blank=True, null=True)
    next_maintenance_date = models.DateField(blank=True, null=True)
    
    class Meta:
        db_table = 'equipment'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['next_maintenance_date']),
        ]
    
    def update_next_maintenance_date(self):
        """Calculate and set the next maintenance date based on last maintenance and interval"""
        if self.last_maintenance_date and self.maintenance_interval_days:
            self.next_maintenance_date = self.last_maintenance_date + datetime.timedelta(days=self.maintenance_interval_days)
    
    def save(self, *args, **kwargs):
        # This replicates the update_next_maintenance_date SQL trigger functionality
        self.update_next_maintenance_date()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class MaintenanceSchedule(BaseModel):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_schedules')
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices, default=MaintenanceType.PREVENTIVE)
    scheduled_date = models.DateField()
    estimated_duration_hours = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    instructions = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=MaintenanceStatus.choices, default=MaintenanceStatus.PLANNED)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_maintenance')
    
    class Meta:
        db_table = 'maintenance_schedule'
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status']),
            models.Index(fields=['equipment', 'status']),
        ]
    
    def __str__(self):
        return f"{self.equipment.code} - {self.get_maintenance_type_display()} on {self.scheduled_date}"


class MaintenanceWorkOrder(BaseModel):
    work_order_number = models.CharField(max_length=50, unique=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='work_orders')
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices)
    description = models.TextField()
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='reported_maintenance')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_work_orders')
    priority = models.CharField(max_length=10, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ], default='MEDIUM')
    status = models.CharField(max_length=20, choices=MaintenanceStatus.choices, default=MaintenanceStatus.PLANNED)
    planned_start_date = models.DateTimeField()
    planned_end_date = models.DateTimeField()
    actual_start_date = models.DateTimeField(blank=True, null=True)
    actual_end_date = models.DateTimeField(blank=True, null=True)
    total_downtime_hours = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')
    
    class Meta:
        db_table = 'maintenance_work_order'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['work_order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_start_date']),
            models.Index(fields=['equipment', 'status']),
        ]
    
    def __str__(self):
        return f"{self.work_order_number} - {self.equipment.name} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Calculate total downtime if actual start and end dates are provided
        if self.actual_start_date and self.actual_end_date:
            delta = self.actual_end_date - self.actual_start_date
            self.total_downtime_hours = delta.total_seconds() / 3600
            
        # Update equipment's last maintenance date if work order is completed
        if self.status == MaintenanceStatus.COMPLETED and self.maintenance_type in [MaintenanceType.PREVENTIVE, MaintenanceType.PREDICTIVE]:
            self.equipment.last_maintenance_date = timezone.now().date()
            self.equipment.update_next_maintenance_date()
            self.equipment.save(update_fields=['last_maintenance_date', 'next_maintenance_date'])
            
        super().save(*args, **kwargs)


class MaintenanceTask(BaseModel):
    work_order = models.ForeignKey(MaintenanceWorkOrder, on_delete=models.CASCADE, related_name='tasks')
    task_description = models.CharField(max_length=200)
    detailed_instructions = models.TextField(blank=True, null=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_tasks')
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
    ], default='PENDING')
    completion_date = models.DateTimeField(blank=True, null=True)
    requires_parts = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'maintenance_task'
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        # Set completion date if status is changed to completed
        if self.status == 'COMPLETED' and not self.completion_date:
            self.completion_date = timezone.now()
            
        super().save(*args, **kwargs)
        
        # Check if all tasks are completed and update work order status if needed
        if self.status == 'COMPLETED':
            work_order = self.work_order
            tasks_count = work_order.tasks.count()
            completed_tasks = work_order.tasks.filter(status='COMPLETED').count()
            
            if tasks_count > 0 and tasks_count == completed_tasks:
                work_order.status = MaintenanceStatus.COMPLETED
                work_order.actual_end_date = timezone.now()
                work_order.save(update_fields=['status', 'actual_end_date'])
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.task_description}"


class MaintenancePart(BaseModel):
    work_order = models.ForeignKey(MaintenanceWorkOrder, on_delete=models.CASCADE, related_name='parts')
    part = models.ForeignKey('inventory.Product', on_delete=models.PROTECT, related_name='maintenance_usage')
    quantity_required = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'maintenance_part'
        unique_together = ['work_order', 'part']
        
    def clean(self):
        if self.quantity_used > self.quantity_required:
            raise ValidationError("Used quantity cannot exceed required quantity")
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.part.product_code}"


class MaintenanceLog(BaseModel):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_logs')
    work_order = models.ForeignKey(MaintenanceWorkOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    maintenance_type = models.CharField(max_length=20, choices=MaintenanceType.choices)
    maintenance_date = models.DateTimeField()
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='performed_maintenance')
    description = models.TextField()
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'maintenance_log'
        ordering = ['-maintenance_date']
        indexes = [
            models.Index(fields=['maintenance_date']),
            models.Index(fields=['equipment']),
            models.Index(fields=['maintenance_type']),
        ]
    
    def __str__(self):
        return f"{self.equipment.code} - {self.get_maintenance_type_display()} on {self.maintenance_date.date()}"


# Calibration and Fixture models (these depend on ControlGauge and Fixture from manufacturing)
class CalibrationStatus(models.TextChoices):
    PASSED = 'PASSED', 'Passed'
    FAILED = 'FAILED', 'Failed'
    PENDING = 'PENDING', 'Pending'
    ADJUSTED = 'ADJUSTED', 'Adjusted and Passed'


class CalibrationRecord(BaseModel):
    control_gauge = models.ForeignKey(ControlGauge, on_delete=models.CASCADE, related_name='calibration_records')
    calibration_date = models.DateField()
    calibrated_by = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=CalibrationStatus.choices)
    certificate_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    next_calibration_date = models.DateField()
    tolerance_values = models.JSONField(blank=True, null=True)
    measured_values = models.JSONField(blank=True, null=True)
    deviations = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'calibration_record'
        ordering = ['-calibration_date']
        indexes = [
            models.Index(fields=['calibration_date']),
            models.Index(fields=['control_gauge']),
            models.Index(fields=['next_calibration_date']),
        ]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update the control gauge's calibration information
        gauge = self.control_gauge
        if self.calibration_date:
            gauge.calibration_date = self.calibration_date
            gauge.upcoming_calibration_date = self.next_calibration_date
            gauge.calibration_certificate = self.certificate_number or ''
            
            # Update gauge status based on calibration result
            if self.status in [CalibrationStatus.PASSED, CalibrationStatus.ADJUSTED]:
                gauge.status = 'AVAILABLE'
            elif self.status == CalibrationStatus.FAILED:
                gauge.status = 'CALIBRATION'
            
            gauge.save(update_fields=[
                'calibration_date', 
                'upcoming_calibration_date', 
                'calibration_certificate', 
                'status'
            ])
    
    def __str__(self):
        return f"{self.control_gauge.code} - Calibrated on {self.calibration_date}"


class FixtureCheckStatus(models.TextChoices):
    PASSED = 'PASSED', 'Passed'
    FAILED = 'FAILED', 'Failed'
    NEEDS_REPAIR = 'NEEDS_REPAIR', 'Needs Repair'
    REPAIRED = 'REPAIRED', 'Repaired'


class FixtureCheck(BaseModel):
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='fixture_checks')
    check_date = models.DateField()
    checked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='fixture_checks')
    status = models.CharField(max_length=20, choices=FixtureCheckStatus.choices)
    notes = models.TextField(blank=True, null=True)
    next_check_date = models.DateField()
    visual_inspection = models.BooleanField(default=True)
    dimensional_check = models.BooleanField(default=False)
    functional_test = models.BooleanField(default=False)
    check_parameters = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'fixture_check'
        ordering = ['-check_date']
        indexes = [
            models.Index(fields=['check_date']),
            models.Index(fields=['fixture']),
            models.Index(fields=['next_check_date']),
        ]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update the fixture's check information
        fixture = self.fixture
        if self.check_date:
            fixture.last_checked = self.check_date
            fixture.next_check_date = self.next_check_date
            
            # Update fixture status based on check result
            if self.status == FixtureCheckStatus.PASSED:
                fixture.status = 'AVAILABLE'
            elif self.status in [FixtureCheckStatus.FAILED, FixtureCheckStatus.NEEDS_REPAIR]:
                fixture.status = 'MAINTENANCE'
            elif self.status == FixtureCheckStatus.REPAIRED:
                fixture.status = 'AVAILABLE'
            
            fixture.save(update_fields=['last_checked', 'next_check_date', 'status'])
    
    def __str__(self):
        return f"{self.fixture.code} - Checked on {self.check_date}"