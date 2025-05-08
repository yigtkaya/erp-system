from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel, User
from inventory.models import Product, ProductBOM
from common.models import FileVersionManager, ContentType


class WorkOrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PLANNED = 'PLANNED', 'Planned'
    RELEASED = 'RELEASED', 'Released'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    ON_HOLD = 'ON_HOLD', 'On Hold'


class WorkOrderPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'


class ProductionLine(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    capacity_per_hour = models.IntegerField(help_text="Units per hour")
    
    class Meta:
        db_table = 'production_lines'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class WorkCenter(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    production_line = models.ForeignKey(ProductionLine, on_delete=models.CASCADE, related_name='work_centers')
    capacity_per_hour = models.IntegerField(help_text="Units per hour")
    setup_time_minutes = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'work_centers'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class WorkOrder(BaseModel):
    work_order_number = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='work_orders')
    quantity_ordered = models.IntegerField()
    quantity_completed = models.IntegerField(default=0)
    quantity_scrapped = models.IntegerField(default=0)
    planned_start_date = models.DateTimeField()
    planned_end_date = models.DateTimeField()
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.DRAFT)
    priority = models.CharField(max_length=10, choices=WorkOrderPriority.choices, default=WorkOrderPriority.MEDIUM)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT, related_name='work_orders')
    sales_order = models.ForeignKey('sales.SalesOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='work_orders')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'work_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['work_order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_start_date']),
        ]
    
    def clean(self):
        if self.planned_end_date <= self.planned_start_date:
            raise ValidationError("Planned end date must be after planned start date")
        
        if self.quantity_completed > self.quantity_ordered:
            raise ValidationError("Completed quantity cannot exceed ordered quantity")
    
    @property
    def completion_percentage(self):
        if self.quantity_ordered == 0:
            return 0
        return (self.quantity_completed / self.quantity_ordered) * 100
    
    @property
    def is_overdue(self):
        if self.status not in [WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED]:
            return timezone.now() > self.planned_end_date
        return False
    
    def __str__(self):
        return f"{self.work_order_number} - {self.product.product_code}"


class WorkOrderOperation(BaseModel):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='operations')
    operation_sequence = models.IntegerField()
    operation_name = models.CharField(max_length=100)
    work_center = models.ForeignKey(WorkCenter, on_delete=models.PROTECT)
    planned_start_date = models.DateTimeField()
    planned_end_date = models.DateTimeField()
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)
    setup_time_minutes = models.IntegerField(default=0)
    run_time_minutes = models.IntegerField()
    quantity_completed = models.IntegerField(default=0)
    quantity_scrapped = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_operations')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'work_order_operations'
        unique_together = ['work_order', 'operation_sequence']
        ordering = ['operation_sequence']
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - Op {self.operation_sequence}: {self.operation_name}"


class MaterialAllocation(BaseModel):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='material_allocations')
    material = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='material_allocations')
    required_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    allocated_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    consumed_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    is_allocated = models.BooleanField(default=False)
    allocation_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'material_allocations'
        unique_together = ['work_order', 'material']
    
    def clean(self):
        if self.allocated_quantity > self.required_quantity:
            raise ValidationError("Allocated quantity cannot exceed required quantity")
    
    @property
    def allocation_percentage(self):
        if self.required_quantity == 0:
            return 0
        return (self.allocated_quantity / self.required_quantity) * 100
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.material.product_code}"


class ProductionOutput(BaseModel):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='outputs')
    operation = models.ForeignKey(WorkOrderOperation, on_delete=models.CASCADE, null=True, blank=True)
    quantity_good = models.IntegerField()
    quantity_scrapped = models.IntegerField(default=0)
    output_date = models.DateTimeField(default=timezone.now)
    operator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='production_outputs')
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'production_outputs'
        ordering = ['-output_date']
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - Output {self.quantity_good} units"


class MachineDowntime(BaseModel):
    work_center = models.ForeignKey(WorkCenter, on_delete=models.CASCADE, related_name='downtimes')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=[
        ('MAINTENANCE', 'Maintenance'),
        ('BREAKDOWN', 'Breakdown'),
        ('SETUP', 'Setup'),
        ('NO_OPERATOR', 'No Operator'),
        ('NO_MATERIAL', 'No Material'),
        ('OTHER', 'Other'),
    ])
    notes = models.TextField(blank=True, null=True)
    reported_by = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'machine_downtimes'
        ordering = ['-start_time']
    
    @property
    def duration_minutes(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None
    
    def __str__(self):
        return f"{self.work_center.code} - {self.reason}"