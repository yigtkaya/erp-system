from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel
from inventory.models import Product, ProductBOM
from common.models import FileVersionManager, ContentType
from datetime import timedelta


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


class MachineType(models.TextChoices):
    CNC_MILLING = 'CNC_MILLING', 'CNC Milling'
    CNC_LATHE = 'CNC_LATHE', 'CNC Lathe'
    DRILLING = 'DRILLING', 'Drilling'
    GRINDING = 'GRINDING', 'Grinding'
    WELDING = 'WELDING', 'Welding'
    ASSEMBLY = 'ASSEMBLY', 'Assembly'
    INSPECTION = 'INSPECTION', 'Inspection'
    OTHER = 'OTHER', 'Other'


class MachineStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    IN_USE = 'IN_USE', 'In Use'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    BROKEN = 'BROKEN', 'Broken'
    RETIRED = 'RETIRED', 'Retired'


class Machine(BaseModel):
    machine_code = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Unique identifier for the machine (e.g., CNC001, MILL02)"
    )
    machine_type = models.CharField(
        max_length=50, 
        choices=MachineType.choices,
        help_text="Type of machine for production planning and scheduling"
    )
    brand = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Manufacturer brand of the machine"
    )
    model = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Model number or name from the manufacturer"
    )
    axis_count = models.CharField(
        max_length=20,
        choices=[
            ('AXIS_2', '2-Axis'),
            ('AXIS_3', '3-Axis'),
            ('AXIS_4', '4-Axis'),
            ('AXIS_5', '5-Axis'),
            ('AXIS_6', '6-Axis'),
            ('MULTI', 'Multi-Axis'),
        ],
        blank=True,
        null=True,
        help_text="Number of axes for machining operations and complexity planning"
    )
    internal_cooling = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Internal cooling pressure in bars for high-speed machining",
        null=True,
        blank=True
    )
    motor_power_kva = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Motor power in KVA for electrical load planning"
    )
    holder_type = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Tool holder type for tool compatibility (e.g., BT40, HSK63)"
    )
    spindle_motor_power_10_percent_kw = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Spindle motor power at 10% duty cycle in kW"
    )
    spindle_motor_power_30_percent_kw = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Spindle motor power at 30% duty cycle in kW"
    )
    power_hp = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Total machine power in horsepower"
    )
    spindle_speed_rpm = models.IntegerField(
        blank=True, 
        null=True,
        help_text="Maximum spindle speed in RPM for cutting speed calculations"
    )
    tool_count = models.IntegerField(
        blank=True, 
        null=True,
        help_text="Number of tool stations available for automatic tool changing"
    )
    nc_control_unit = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Numerical control unit brand and model (e.g., Fanuc 0i-MF)"
    )
    manufacturing_year = models.DateField(
        null=True, 
        blank=True,
        help_text="Year the machine was manufactured for depreciation tracking"
    )
    serial_number = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Manufacturer's serial number for warranty and service tracking"
    )
    machine_weight_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Machine weight in kilograms for floor loading calculations"
    )
    max_part_size = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Maximum workpiece dimensions (e.g., 500x400x300mm)"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes and specifications about the machine"
    )
    status = models.CharField(
        max_length=20, 
        choices=MachineStatus.choices, 
        default=MachineStatus.AVAILABLE,
        help_text="Current operational status for production planning"
    )
    maintenance_interval = models.IntegerField(
        help_text="Days between required maintenance cycles",
        default=90
    )
    last_maintenance_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Date of the last completed maintenance"
    )
    next_maintenance_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Calculated date for next scheduled maintenance"
    )
    maintenance_notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Notes from maintenance activities and service history"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this machine is available for production scheduling"
    )

    class Meta:
        db_table = 'machines'
        ordering = ['machine_code']
        indexes = [
            models.Index(fields=['machine_code']),
            models.Index(fields=['status']),
            models.Index(fields=['machine_type']),
            models.Index(fields=['next_maintenance_date']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_maintenance_date']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['status', 'machine_type']),
            models.Index(fields=['machine_type', 'is_active']),
        ]

    def __str__(self):
        return f"{self.machine_code} - {self.machine_type}"

    def calculate_next_maintenance(self):
        """Calculate and update the next maintenance date"""
        if self.last_maintenance_date:
            self.next_maintenance_date = self.last_maintenance_date + timedelta(days=self.maintenance_interval)
            self.save(update_fields=['next_maintenance_date'])

    def save(self, *args, **kwargs):
        # Auto-calculate next maintenance date if last maintenance date is set
        if self.last_maintenance_date and self.maintenance_interval:
            self.next_maintenance_date = self.last_maintenance_date + timedelta(days=self.maintenance_interval)
        super().save(*args, **kwargs)

    @property
    def is_maintenance_overdue(self):
        """Check if maintenance is overdue"""
        if not self.next_maintenance_date:
            return False
        return timezone.now().date() > self.next_maintenance_date


class WorkOrder(BaseModel):
    work_order_number = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Unique work order identifier for tracking production"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.PROTECT, 
        related_name='work_orders',
        help_text="Product to be manufactured in this work order"
    )
    quantity_ordered = models.IntegerField(
        help_text="Total quantity to be produced"
    )
    quantity_completed = models.IntegerField(
        default=0,
        help_text="Quantity successfully completed so far"
    )
    quantity_scrapped = models.IntegerField(
        default=0,
        help_text="Quantity rejected due to quality issues"
    )
    planned_start_date = models.DateTimeField(
        help_text="Scheduled start date and time for production"
    )
    planned_end_date = models.DateTimeField(
        help_text="Scheduled completion date and time"
    )
    actual_start_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Actual date and time production started"
    )
    actual_end_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Actual date and time production completed"
    )
    status = models.CharField(
        max_length=20, 
        choices=WorkOrderStatus.choices, 
        default=WorkOrderStatus.DRAFT,
        help_text="Current status of the work order"
    )
    priority = models.CharField(
        max_length=10, 
        choices=WorkOrderPriority.choices, 
        default=WorkOrderPriority.MEDIUM,
        help_text="Priority level for production scheduling"
    )
    primary_machine = models.ForeignKey(
        Machine, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='primary_work_orders',
        help_text="Primary machine assigned for this work order"
    )
    sales_order = models.ForeignKey(
        'sales.SalesOrder', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='work_orders',
        help_text="Source sales order that triggered this production"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional instructions or notes for production"
    )
    
    class Meta:
        db_table = 'work_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['work_order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_start_date']),
            models.Index(fields=['primary_machine']),
            models.Index(fields=['priority']),
            models.Index(fields=['product']),
            models.Index(fields=['planned_end_date']),
            models.Index(fields=['actual_start_date']),
            models.Index(fields=['actual_end_date']),
            models.Index(fields=['sales_order']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['status', 'planned_start_date']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['primary_machine', 'status']),
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
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, related_name='operations', null=True, blank=True)
    planned_start_date = models.DateTimeField()
    planned_end_date = models.DateTimeField()
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)
    setup_time_minutes = models.IntegerField(default=0)
    run_time_minutes = models.IntegerField()
    quantity_completed = models.IntegerField(default=0)
    quantity_scrapped = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_operations')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'work_order_operations'
        unique_together = ['work_order', 'operation_sequence']
        ordering = ['operation_sequence']
        indexes = [
            models.Index(fields=['machine']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_start_date']),
            models.Index(fields=['work_order']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['planned_end_date']),
            models.Index(fields=['actual_start_date']),
            models.Index(fields=['actual_end_date']),
            models.Index(fields=['work_order', 'status']),
            models.Index(fields=['machine', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def clean(self):
        pass
    
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
        indexes = [
            models.Index(fields=['work_order']),
            models.Index(fields=['material']),
            models.Index(fields=['is_allocated']),
            models.Index(fields=['allocation_date']),
            models.Index(fields=['work_order', 'is_allocated']),
            models.Index(fields=['material', 'is_allocated']),
        ]
    
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
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='production_outputs')
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'production_outputs'
        ordering = ['-output_date']
        indexes = [
            models.Index(fields=['work_order']),
            models.Index(fields=['operation']),
            models.Index(fields=['operator']),
            models.Index(fields=['output_date']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['work_order', 'output_date']),
            models.Index(fields=['operator', 'output_date']),
        ]
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - Output {self.quantity_good} units"


class MachineDowntime(BaseModel):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='downtimes', null=True, blank=True)
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
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'machine_downtimes'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['machine']),
            models.Index(fields=['start_time']),
            models.Index(fields=['category']),
            models.Index(fields=['end_time']),
            models.Index(fields=['reported_by']),
            models.Index(fields=['machine', 'category']),
            models.Index(fields=['machine', 'start_time']),
            models.Index(fields=['category', 'start_time']),
        ]
    
    @property
    def duration_minutes(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return None
    
    def __str__(self):
        return f"{self.machine.machine_code} - {self.reason}"


# New models for ProcessConfig and workflow functionality
class AxisCount(models.TextChoices):
    AXIS_2 = 'AXIS_2', '2-Axis'
    AXIS_3 = 'AXIS_3', '3-Axis'
    AXIS_4 = 'AXIS_4', '4-Axis'
    AXIS_5 = 'AXIS_5', '5-Axis'
    AXIS_6 = 'AXIS_6', '6-Axis'
    MULTI = 'MULTI', 'Multi-Axis'


class ManufacturingProcess(BaseModel):
    process_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    machine_type = models.CharField(max_length=50)
    standard_setup_time = models.IntegerField(help_text="Setup time in minutes", default=0)
    standard_runtime = models.IntegerField(help_text="Runtime per unit in minutes", default=0)
    
    class Meta:
        db_table = 'manufacturing_process'
        ordering = ['process_code']
        indexes = [
            models.Index(fields=['process_code']),
            models.Index(fields=['machine_type']),
            models.Index(fields=['name']),
            models.Index(fields=['machine_type', 'name']),
        ]
    
    def __str__(self):
        return f"{self.process_code} - {self.name}"


class WorkflowStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    REVIEW = 'REVIEW', 'Under Review'
    ACTIVE = 'ACTIVE', 'Active'
    OBSOLETE = 'OBSOLETE', 'Obsolete'
    ARCHIVED = 'ARCHIVED', 'Archived'


class ProductWorkflow(BaseModel):
    product = models.ForeignKey('inventory.Product', on_delete=models.CASCADE, related_name='workflows')
    version = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=WorkflowStatus.choices, default=WorkflowStatus.DRAFT)
    effective_date = models.DateField(null=True, blank=True)
    revision_notes = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_workflows')
    approval_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'product_workflow'
        unique_together = ['product', 'version']
        ordering = ['product', '-version']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['status']),
            models.Index(fields=['effective_date']),
            models.Index(fields=['approved_by']),
            models.Index(fields=['approval_date']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['status', 'effective_date']),
        ]
    
    def clean(self):
        # Replicate the ensure_single_active_workflow trigger logic
        if self.status == WorkflowStatus.ACTIVE:
            # Check for other active workflows for this product
            active_workflows = ProductWorkflow.objects.filter(
                product=self.product,
                status=WorkflowStatus.ACTIVE
            ).exclude(pk=self.pk)
            
            # If there are any, set their status to obsolete
            if active_workflows.exists():
                active_workflows.update(status=WorkflowStatus.OBSOLETE)
    
    def save(self, *args, **kwargs):
        self.clean()  # Run validation
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.product_code} workflow v{self.version} ({self.get_status_display()})"


class ProcessConfigStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    REVIEW = 'REVIEW', 'Under Review'
    ACTIVE = 'ACTIVE', 'Active'
    OBSOLETE = 'OBSOLETE', 'Obsolete'


class ProcessConfig(BaseModel):
    workflow = models.ForeignKey(ProductWorkflow, on_delete=models.CASCADE, related_name='process_configs')
    process = models.ForeignKey(ManufacturingProcess, on_delete=models.PROTECT)
    sequence_order = models.IntegerField()
    version = models.CharField(max_length=20, default='1.0')
    status = models.CharField(max_length=20, choices=ProcessConfigStatus.choices, default=ProcessConfigStatus.DRAFT)
    
    # Machine requirements
    machine_type = models.CharField(max_length=50, blank=True, null=True)
    axis_count = models.CharField(max_length=10, choices=AxisCount.choices, blank=True, null=True)
    
    # Tool and fixture requirements
    tool = models.ForeignKey('inventory.Tool', on_delete=models.SET_NULL, null=True, blank=True)
    fixture = models.ForeignKey('Fixture', on_delete=models.SET_NULL, null=True, blank=True)
    control_gauge = models.ForeignKey('ControlGauge', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Time estimates
    setup_time = models.IntegerField(help_text="Setup time in minutes", default=0)
    cycle_time = models.IntegerField(help_text="Cycle time per unit in seconds", default=0)
    
    # Process parameters
    parameters = models.JSONField(null=True, blank=True)
    quality_requirements = models.JSONField(null=True, blank=True)
    instructions = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'process_config'
        unique_together = ['workflow', 'sequence_order', 'version']
        ordering = ['workflow', 'sequence_order', '-version']
        indexes = [
            models.Index(fields=['workflow']),
            models.Index(fields=['process']),
            models.Index(fields=['status']),
            models.Index(fields=['machine_type']),
            models.Index(fields=['axis_count']),
            models.Index(fields=['tool']),
            models.Index(fields=['fixture']),
            models.Index(fields=['control_gauge']),
            models.Index(fields=['workflow', 'status']),
            models.Index(fields=['process', 'status']),
            models.Index(fields=['machine_type', 'axis_count']),
        ]
    
    def clean(self):
        # Replicate the ensure_single_active_process_config trigger logic
        if self.status == ProcessConfigStatus.ACTIVE:
            # Check for other active process configs with same workflow, sequence, process
            active_configs = ProcessConfig.objects.filter(
                workflow=self.workflow,
                sequence_order=self.sequence_order,
                process=self.process,
                status=ProcessConfigStatus.ACTIVE
            ).exclude(pk=self.pk)
            
            # If there are any, set their status to obsolete
            if active_configs.exists():
                active_configs.update(status=ProcessConfigStatus.OBSOLETE)
    
    def save(self, *args, **kwargs):
        self.clean()  # Run validation
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.workflow.product.product_code} - Step {self.sequence_order}: {self.process.name} v{self.version}"


class FixtureStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    IN_USE = 'IN_USE', 'In Use'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    BROKEN = 'BROKEN', 'Broken'
    RETIRED = 'RETIRED', 'Retired'


class Fixture(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    fixture_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=FixtureStatus.choices, default=FixtureStatus.AVAILABLE)
    location = models.CharField(max_length=100, null=True, blank=True)
    check_interval_days = models.IntegerField(default=90)
    last_checked = models.DateField(null=True, blank=True)
    next_check_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'fixture'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['next_check_date']),
            models.Index(fields=['fixture_type']),
            models.Index(fields=['location']),
            models.Index(fields=['last_checked']),
            models.Index(fields=['status', 'fixture_type']),
            models.Index(fields=['status', 'next_check_date']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate next check date when last_checked is updated
        if self.last_checked and self.check_interval_days:
            self.next_check_date = self.last_checked + timezone.timedelta(days=self.check_interval_days)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.get_status_display()})"


class GaugeStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    IN_USE = 'IN_USE', 'In Use'
    CALIBRATION = 'CALIBRATION', 'Under Calibration'
    BROKEN = 'BROKEN', 'Broken'
    RETIRED = 'RETIRED', 'Retired'


class ControlGauge(BaseModel):
    stock_name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=GaugeStatus.choices, default=GaugeStatus.AVAILABLE)
    calibration_date = models.DateField(null=True, blank=True)
    calibration_interval_days = models.IntegerField(default=365)
    upcoming_calibration_date = models.DateField(null=True, blank=True)
    calibration_certificate = models.CharField(max_length=100, null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'control_gauge'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['upcoming_calibration_date']),
            models.Index(fields=['calibration_date']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['stock_name']),
            models.Index(fields=['status', 'upcoming_calibration_date']),
            models.Index(fields=['manufacturer', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate upcoming calibration date when calibration_date is updated
        if self.calibration_date and self.calibration_interval_days:
            self.upcoming_calibration_date = self.calibration_date + timezone.timedelta(days=self.calibration_interval_days)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.code} - {self.stock_name} ({self.get_status_display()})"


# Model for SubWorkOrder
class SubWorkOrder(BaseModel):
    parent_work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='sub_work_orders')
    bom_component = models.ForeignKey('inventory.ProductBOM', on_delete=models.SET_NULL, null=True, blank=True)
    work_order_number = models.CharField(max_length=50, unique=True)
    quantity_ordered = models.IntegerField()
    quantity_completed = models.IntegerField(default=0)
    quantity_scrapped = models.IntegerField(default=0)
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    target_category = models.ForeignKey('inventory.InventoryCategory', on_delete=models.PROTECT)
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'sub_work_order'
        ordering = ['planned_start']
        indexes = [
            models.Index(fields=['parent_work_order']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_start']),
            models.Index(fields=['target_category']),
            models.Index(fields=['work_order_number']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['planned_end']),
            models.Index(fields=['actual_start']),
            models.Index(fields=['actual_end']),
            models.Index(fields=['bom_component']),
            models.Index(fields=['parent_work_order', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['target_category', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update parent work order completion percentage
        # This replicates the update_parent_work_order_completion trigger
        parent_work_order = self.parent_work_order
        total_sub_orders = parent_work_order.sub_work_orders.count()
        completed_sub_orders = parent_work_order.sub_work_orders.filter(status=WorkOrderStatus.COMPLETED).count()
        
        if total_sub_orders > 0:
            completion_pct = (completed_sub_orders / total_sub_orders) * 100
            parent_work_order.completion_percentage = completion_pct
            parent_work_order.save(update_fields=['completion_percentage'])
    
    def clean(self):
        # Replicate the validate_sub_work_order_target_category trigger logic
        if self.bom_component and self.target_category:
            component_product = self.bom_component.child_product
            allowed_categories = []
            
            if component_product.product_type == 'SINGLE':
                allowed_categories = ['HAMMADDE', 'KARANTINA', 'HURDA']
            elif component_product.product_type == 'SEMI':
                allowed_categories = ['PROSES', 'MAMUL', 'KARANTINA', 'HURDA']
            elif component_product.product_type == 'MONTAGED':
                allowed_categories = ['MAMUL', 'KARANTINA', 'HURDA']
            
            if self.target_category.name not in allowed_categories:
                raise ValidationError(f"Invalid target category for product type {component_product.product_type}. "
                                     f"Allowed categories: {', '.join(allowed_categories)}")
    
    def __str__(self):
        return f"Sub-WO: {self.work_order_number} - {self.completion_percentage}% complete"


# Audit Log Model for Manufacturing Operations
class ManufacturingAuditLog(BaseModel):
    """
    Database model to store manufacturing operation audit trail
    """
    LOG_LEVELS = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    ACTION_TYPES = [
        ('WORK_ORDER_CREATE', 'Work Order Created'),
        ('WORK_ORDER_UPDATE', 'Work Order Updated'),
        ('WORK_ORDER_START', 'Work Order Started'),
        ('WORK_ORDER_COMPLETE', 'Work Order Completed'),
        ('WORK_ORDER_CANCEL', 'Work Order Cancelled'),
        ('MATERIAL_ALLOCATE', 'Materials Allocated'),
        ('MATERIAL_ISSUE', 'Materials Issued'),
        ('PRODUCTION_RECORD', 'Production Output Recorded'),
        ('MACHINE_STATUS_CHANGE', 'Machine Status Changed'),
        ('MACHINE_MAINTENANCE', 'Machine Maintenance Recorded'),
        ('OPERATION_START', 'Operation Started'),
        ('OPERATION_COMPLETE', 'Operation Completed'),
        ('DOWNTIME_RECORD', 'Downtime Recorded'),
        ('API_REQUEST', 'API Request'),
        ('BUSINESS_RULE_VIOLATION', 'Business Rule Violation'),
        ('SYSTEM_ERROR', 'System Error'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="User who performed the action"
    )
    log_level = models.CharField(
        max_length=10, 
        choices=LOG_LEVELS, 
        default='INFO',
        help_text="Severity level of the log entry"
    )
    action_type = models.CharField(
        max_length=30, 
        choices=ACTION_TYPES,
        help_text="Type of action performed"
    )
    entity_type = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Type of entity affected (WorkOrder, Machine, etc.)"
    )
    entity_id = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="ID of the affected entity"
    )
    message = models.TextField(
        help_text="Human-readable log message"
    )
    details = models.JSONField(
        null=True, 
        blank=True,
        help_text="Additional structured data"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        null=True, 
        blank=True,
        help_text="User agent string"
    )
    
    class Meta:
        db_table = 'manufacturing_audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['log_level']),
            models.Index(fields=['action_type']),
            models.Index(fields=['entity_type']),
            models.Index(fields=['entity_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'action_type']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['log_level', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_log_level_display()}: {self.get_action_type_display()} by {self.user or 'System'}"
    
    @classmethod
    def log_action(cls, user, action_type, message, log_level='INFO', entity_type=None, 
                   entity_id=None, details=None, ip_address=None, user_agent=None):
        """Create a new audit log entry"""
        return cls.objects.create(
            user=user,
            log_level=log_level,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )