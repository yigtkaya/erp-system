from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer, ProductType, ComponentType, MachineStatus, WorkOrderStatus
from sales.models import SalesOrderItem
from datetime import datetime, timedelta
from django.db.models import Q
from django.db.models.query import QuerySet
from model_utils.managers import InheritanceManager
from django.utils import timezone

class AxisCount(models.TextChoices):
    NINE_AXIS = '9EKSEN', '9 Eksen'
    EIGHT_POINT_FIVE_AXIS = '8.5EKSEN', '8.5 Eksen'
    FIVE_AXIS = '5EKSEN', '5 Eksen'
    FOUR_AXIS = '4EKSEN', '4 Eksen'
    THREE_AXIS = '3EKSEN', '3 Eksen'
    TWO_AXIS = '2EKSEN', '2 Eksen'
    ONE_AXIS = '1EKSEN', '1 Eksen'


class MachineType(models.TextChoices):
    PROCESSING_CENTER = 'İşleme Merkezi', 'İşleme Merkezi'
    CNC_TORNA = 'CNC Torna Merkezi', 'CNC Torna Merkezi'
    CNC_KAYAR_OTOMAT = 'CNC Kayar Otomat', 'CNC Kayar Otomat'
    NONE = 'Yok', 'Yok'

class Machine(BaseModel):
    machine_code = models.CharField(max_length=50, unique=True)
    machine_type = models.CharField(max_length=50, choices=MachineType.choices)
    brand = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    axis_count = models.CharField(
        max_length=20,
        choices=AxisCount.choices,
        blank=True,
        null=True
    )
    internal_cooling = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Internal cooling pressure in bars",
        null=True,
        blank=True
    )
    motor_power_kva = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    holder_type = models.CharField(max_length=50, blank=True, null=True)
    spindle_motor_power_10_percent_kw = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    spindle_motor_power_30_percent_kw = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    power_hp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    spindle_speed_rpm = models.IntegerField(blank=True, null=True)
    tool_count = models.IntegerField(blank=True, null=True)
    nc_control_unit = models.CharField(max_length=50, blank=True, null=True)
    manufacturing_year = models.DateField(null=True, blank=True)
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True)
    machine_weight_kg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_part_size = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=MachineStatus.choices, default=MachineStatus.AVAILABLE)
    maintenance_interval = models.IntegerField(
        help_text="Days between required maintenance",
        default=90
    )
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    maintenance_notes = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['machine_type']),
        ]

    def __str__(self):
        return f"{self.machine_code} - {self.machine_type}"

    def calculate_next_maintenance(self):
        if self.last_maintenance_date:
            self.next_maintenance_date = self.last_maintenance_date + timedelta(days=self.maintenance_interval)
            self.save()

class ManufacturingProcess(BaseModel):
    process_code = models.CharField(max_length=50, unique=True)
    process_name = models.CharField(max_length=100)
    standard_time_minutes = models.IntegerField()
    machine_type = models.CharField(max_length=50, choices=MachineType.choices)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_processes')

    class Meta:
        indexes = [
            models.Index(fields=['process_code']),
            models.Index(fields=['machine_type']),
        ]

    def __str__(self):
        return f"{self.process_code} - {self.process_name}"

class BOM(BaseModel):
    """
    The BOM is associated with a product that is manufactured.
    """
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        to_field='product_code'
    )
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_boms'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    parent_bom = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='derived_boms',
        help_text="The BOM this version was derived from"
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Bill of Materials"
        verbose_name_plural = "Bills of Materials"
        unique_together = ['product', 'version']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_approved']),
        ]

    def clean(self):
        super().clean()
        # Only validate that Standard products cannot have BOMs
        if self.product.product_type == ProductType.STANDARD_PART:
            raise ValidationError("Standard products (bought externally) cannot have a BOM")

    def approve(self, user):
        """
        Approve the BOM, setting approved_by and approved_at fields.
        """
        if self.is_approved:
            return False
        
        self.is_approved = True
        self.approved_by = user
        self.approved_at = timezone.now()
        self.save()
        return True
    
    def create_new_version(self, new_version=None):
        """
        Create a new version of this BOM.
        
        Args:
            new_version: Optional version string. If not provided, increments the current version.
            
        Returns:
            A new BOM instance with copied components.
        """
        if not new_version:
            # Parse current version and increment
            try:
                major, minor = self.version.split('.')
                new_version = f"{major}.{int(minor) + 1}"
            except ValueError:
                # If version format is not as expected, just append .1
                new_version = f"{self.version}.1"
        
        # Create new BOM
        new_bom = BOM.objects.create(
            product=self.product,
            version=new_version,
            is_active=True,
            is_approved=False,  # New versions start unapproved
            parent_bom=self,
            notes=f"Derived from version {self.version}"
        )
        
        # Copy all components
        for component in self.components.all():
            BOMComponent.objects.create(
                bom=new_bom,
                sequence_order=component.sequence_order,
                quantity=component.quantity,
                notes=component.notes,
                lead_time_days=component.lead_time_days,
                product=component.product
            )
        
        return new_bom
    
    def __str__(self):
        return f"{self.product.product_code} - v{self.version}"

class BOMComponent(BaseModel):
    """
    A BOM component that represents a product used in manufacturing.
    Each component must have a reference to a product and a quantity.
    """
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='components')
    sequence_order = models.IntegerField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    notes = models.TextField(blank=True)
    lead_time_days = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Expected lead time in days for this component"
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        help_text="Reference to the product used in this component"
    )

    class Meta:
        ordering = ['sequence_order']
        unique_together = [('bom', 'sequence_order')]
        indexes = [
            models.Index(fields=['bom']),
            models.Index(fields=['sequence_order'])
        ]

    def clean(self):
        super().clean()
        # Check for duplicate sequence_order within the same BOM
        if self.bom_id is not None and self.sequence_order is not None:
            duplicate_exists = BOMComponent.objects.filter(
                bom=self.bom,
                sequence_order=self.sequence_order
            ).exclude(pk=self.pk).exists()
            
            if duplicate_exists:
                raise ValidationError({
                    'sequence_order': f'A component with sequence order {self.sequence_order} already exists in this BOM.'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_code} x{self.quantity}"

class WorkflowProcess(BaseModel):
    """
    Represents a manufacturing process step in the workflow.
    Each process has a process number and stock code for tracking.
    Some processes may not require machines (e.g., manual assembly, quality control).
    """
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        related_name='workflow_processes',
        help_text="Product this workflow process belongs to"
    )
    process = models.ForeignKey(ManufacturingProcess, on_delete=models.PROTECT)
    process_number = models.CharField(max_length=50, unique=True, help_text="Unique process number for tracking")
    stock_code = models.CharField(max_length=50, help_text="Stock code for the process output")
    raw_material = models.ForeignKey('inventory.RawMaterial', on_delete=models.PROTECT, null=True, blank=True)
    axis_count = models.CharField(
        max_length=20,
        choices=AxisCount.choices,
        help_text="Required machine axis count (only if process requires a machine)",
        blank=True,
        null=True
    )
    estimated_duration_minutes = models.IntegerField(blank=True, null=True)
    tooling_requirements = models.TextField(blank=True, null=True)
    quality_checks = models.TextField(blank=True, null=True)
    sequence_order = models.IntegerField(
        help_text="Order of this process in the product's workflow"
    )

    class Meta:
        verbose_name = "Workflow Process"
        verbose_name_plural = "Workflow Processes"
        ordering = ['product', 'sequence_order']
        unique_together = [('product', 'sequence_order')]
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['process_number']),
            models.Index(fields=['stock_code']),
        ]

    def clean(self):
        super().clean()
        # Validate axis_count based on requires_machine
        if self.requires_machine:
            if not self.axis_count:
                raise ValidationError("Axis count is required when process requires a machine")
        else:
            if self.axis_count:
                raise ValidationError("Axis count should not be set for processes that don't require machines")

        # Check for duplicate sequence_order within the same product
        if self.product_id is not None and self.sequence_order is not None:
            duplicate_exists = WorkflowProcess.objects.filter(
                product=self.product,
                sequence_order=self.sequence_order
            ).exclude(pk=self.pk).exists()
            
            if duplicate_exists:
                raise ValidationError({
                    'sequence_order': f'A process with sequence order {self.sequence_order} already exists for this product.'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_code} - {self.process_number} - {self.process.process_name}"

class WorkOrderStatusTransition:
    """
    Defines valid status transitions for work orders.
    """
    VALID_TRANSITIONS = {
        WorkOrderStatus.PLANNED: [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.DELAYED],
        WorkOrderStatus.IN_PROGRESS: [WorkOrderStatus.DELAYED, WorkOrderStatus.COMPLETED],
        WorkOrderStatus.DELAYED: [WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.COMPLETED],
        WorkOrderStatus.COMPLETED: [],  # No transitions from completed
    }
    
    @classmethod
    def is_valid_transition(cls, from_status, to_status):
        """
        Check if a status transition is valid.
        
        Args:
            from_status: Current status
            to_status: Target status
            
        Returns:
            bool: True if transition is valid, False otherwise
        """
        if from_status == to_status:
            return True  # Same status is always valid
            
        valid_next_statuses = cls.VALID_TRANSITIONS.get(from_status, [])
        return to_status in valid_next_statuses

class WorkOrder(BaseModel):
    order_number = models.CharField(max_length=50, unique=True)
    sales_order_item = models.ForeignKey(SalesOrderItem, on_delete=models.PROTECT)
    bom = models.ForeignKey(BOM, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    planned_start = models.DateField()
    planned_end = models.DateField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)
    priority = models.IntegerField(default=1)  # 1 is highest priority
    notes = models.TextField(blank=True, null=True)
    completion_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Percentage of work completed"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_work_orders'
    )

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['planned_start']),
            models.Index(fields=['planned_end']),
        ]
    
    def clean(self):
        super().clean()
        if self.planned_end < self.planned_start:
            raise ValidationError("Planned end date cannot be before planned start date")
            
        # Validate BOM is approved
        if not self.bom.is_approved:
            raise ValidationError("Cannot create work order with unapproved BOM")
    
    def update_status(self, new_status, user=None):
        """
        Update the work order status with proper validation and tracking.
        
        Args:
            new_status: The new status to set
            user: The user making the change (optional)
            
        Returns:
            bool: True if status was updated, False otherwise
            
        Raises:
            ValidationError: If the status transition is invalid
        """
        if not WorkOrderStatusTransition.is_valid_transition(self.status, new_status):
            raise ValidationError(f"Invalid status transition from {self.status} to {new_status}")
            
        old_status = self.status
        self.status = new_status
        
        # Update timestamps based on status
        now = timezone.now()
        if old_status == WorkOrderStatus.PLANNED and new_status == WorkOrderStatus.IN_PROGRESS:
            self.actual_start = now
        elif new_status == WorkOrderStatus.COMPLETED:
            self.actual_end = now
            self.completion_percentage = 100
            
        # Create status change record
        WorkOrderStatusChange.objects.create(
            work_order=self,
            from_status=old_status,
            to_status=new_status,
            changed_by=user,
            changed_at=now,
            notes=f"Status changed from {old_status} to {new_status}"
        )
        
        self.save()
        
        # Update sub work orders if parent status changes
        if new_status in [WorkOrderStatus.COMPLETED]:
            for sub_order in self.sub_orders.exclude(status__in=[WorkOrderStatus.COMPLETED]):
                try:
                    sub_order.update_status(new_status, user)
                except ValidationError:
                    # Log but continue with other sub orders
                    pass
                    
        return True
    
    def calculate_completion_percentage(self):
        """
        Calculate and update the completion percentage based on sub work orders.
        """
        sub_orders = self.sub_orders.all()
        if not sub_orders.exists():
            return
            
        completed_sub_orders = sub_orders.filter(status=WorkOrderStatus.COMPLETED).count()
        total_sub_orders = sub_orders.count()
        
        if total_sub_orders > 0:
            self.completion_percentage = (completed_sub_orders / total_sub_orders) * 100
            self.save(update_fields=['completion_percentage'])
    
    def create_sub_work_orders(self):
        """
        Automatically create sub work orders for all components in the BOM.
        """
        if self.sub_orders.exists():
            return  # Sub orders already exist
            
        # Get all components from the BOM
        components = self.bom.components.all()
        
        # Calculate dates based on lead times and dependencies
        for component in components:
            # Default dates if no specific scheduling logic
            start_date = self.planned_start
            end_date = self.planned_end
            
            # Create the sub work order
            sub_order = SubWorkOrder.objects.create(
                parent_work_order=self,
                bom_component=component,
                quantity=self.quantity * component.quantity if component.quantity else self.quantity,
                planned_start=start_date,
                planned_end=end_date,
                status=WorkOrderStatus.PLANNED
            )
            
            # For process components, create process steps
            if component.material.product_type == ProductType.SEMI:
                # Create a process step for the workflow process
                workflow_process = WorkflowProcess.objects.filter(
                    product=component.material,
                    raw_material=component.material
                ).first()
                
                if workflow_process:
                    SubWorkOrderProcess.objects.create(
                        sub_work_order=sub_order,
                        workflow_process=workflow_process,
                        sequence_order=1,
                        planned_duration_minutes=workflow_process.estimated_duration_minutes
                    )

    def __str__(self):
        return f"{self.order_number} - {self.bom.product.product_code}"

class WorkOrderStatusChange(BaseModel):
    """
    Tracks status changes for work orders.
    """
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='status_changes')
    from_status = models.CharField(max_length=20, choices=WorkOrderStatus.choices)
    to_status = models.CharField(max_length=20, choices=WorkOrderStatus.choices)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['work_order']),
            models.Index(fields=['changed_at']),
        ]
        
    def __str__(self):
        return f"{self.work_order.order_number}: {self.from_status} → {self.to_status}"

class SubWorkOrder(BaseModel):
    """
    A sub–work order is linked to a parent work order and corresponds to one BOM component.
    
    For Montaged products, these sub–work orders are typically created for the Semi components.
    """
    parent_work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='sub_orders')
    bom_component = models.ForeignKey(BOMComponent, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    planned_start = models.DateField()
    planned_end = models.DateField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)
    output_quantity = models.IntegerField(null=True, blank=True)
    scrap_quantity = models.IntegerField(default=0)
    target_category = models.ForeignKey('inventory.InventoryCategory', on_delete=models.PROTECT, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    completion_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        help_text="Percentage of work completed"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sub_work_orders'
    )

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['parent_work_order']),
            models.Index(fields=['planned_start']),
            models.Index(fields=['planned_end']),
        ]

    @property
    def component_type(self):
        """Returns the type of BOM component"""
        return self.bom_component.material.product_type

    @property
    def is_process_component(self):
        """Check if this sub work order is for a process component"""
        return self.bom_component.material.product_type == ProductType.SEMI

    @property
    def is_product_component(self):
        """Check if this sub work order is for a product component"""
        return self.bom_component.material.product_type == ProductType.MONTAGED

    def get_specific_component(self):
        """Get the BOMComponent instance"""
        return self.bom_component
        
    def update_status(self, new_status, user=None):
        """
        Update the sub work order status with proper validation and tracking.
        
        Args:
            new_status: The new status to set
            user: The user making the change (optional)
            
        Returns:
            bool: True if status was updated, False otherwise
            
        Raises:
            ValidationError: If the status transition is invalid
        """
        if not WorkOrderStatusTransition.is_valid_transition(self.status, new_status):
            raise ValidationError(f"Invalid status transition from {self.status} to {new_status}")
            
        old_status = self.status
        self.status = new_status
        
        # Update timestamps based on status
        now = timezone.now()
        if old_status == WorkOrderStatus.PLANNED and new_status == WorkOrderStatus.IN_PROGRESS:
            self.actual_start = now
        elif new_status == WorkOrderStatus.COMPLETED:
            self.actual_end = now
            self.completion_percentage = 100
            
        self.save()
        
        # Update parent work order completion percentage
        self.parent_work_order.calculate_completion_percentage()
                    
        return True

    def clean(self):
        super().clean()
        if self.output_quantity and self.output_quantity + self.scrap_quantity > self.quantity:
            raise ValidationError("Output quantity plus scrap cannot exceed input quantity")
        
        if self.status == WorkOrderStatus.COMPLETED and not self.output_quantity:
            raise ValidationError("Output quantity must be set when completing a work order")

        # Validate target category based on component type
        if self.target_category:
            component = self.bom_component
            if component.material.product_type == ProductType.SEMI:
                # For Semi or Single products using process components the finished goods
                # (raw processed items) should go to the 'PROSES' category.
                if self.target_category.name != 'PROSES':
                    raise ValidationError("Processed Semi/Single products must target Proses category")
            elif component.material.product_type == ProductType.MONTAGED:
                # For Montaged product BOMs the product components (usually Semi sub–assemblies)
                # should target the 'MAMUL' category.
                if self.target_category.name != 'MAMUL':
                    raise ValidationError("Montaged product components must target Mamul category")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        component = self.bom_component
        if component.material.product_type == ProductType.SEMI:
            return f"{self.parent_work_order.order_number} - Process: {component.material.material_code if component.material else 'No Material'}"
        else:
            return f"{self.parent_work_order.order_number} - Product: {component.material.product_code if component.material else 'No Product'}"

class SubWorkOrderProcess(models.Model):
    """
    For sub work orders, you can track the individual process steps.
    Each process has a unique process number and stock code.
    """
    PROCESS_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SETUP', 'Machine Setup'),
        ('RUNNING', 'Running'),
        ('PAUSED', 'Paused'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]
    
    sub_work_order = models.ForeignKey(SubWorkOrder, on_delete=models.CASCADE, related_name='processes')
    workflow_process = models.ForeignKey(WorkflowProcess, on_delete=models.PROTECT, null=True)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, null=True, blank=True)
    sequence_order = models.IntegerField()
    planned_duration_minutes = models.IntegerField(null=True, blank=True)
    actual_duration_minutes = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PROCESS_STATUS_CHOICES, default='PENDING')
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='operated_processes')
    setup_time_minutes = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['sequence_order']
        indexes = [
            models.Index(fields=['sub_work_order']),
            models.Index(fields=['workflow_process']),
            models.Index(fields=['machine']),
            models.Index(fields=['status']),
            models.Index(fields=['start_time']),
            models.Index(fields=['end_time']),
        ]

    def clean(self):
        super().clean()
        # Validate machine requirements against the workflow process
        if self.machine and self.workflow_process:
            if self.workflow_process.axis_count and self.machine.axis_count != self.workflow_process.axis_count:
                raise ValidationError("Machine axis count does not match process requirements")
            if self.machine.machine_type != self.workflow_process.process.machine_type:
                raise ValidationError("Machine type does not match process requirements")
            if self.machine.status != MachineStatus.AVAILABLE:
                raise ValidationError("Selected machine is not available")
                
        # Validate time tracking
        if self.end_time and self.start_time and self.end_time < self.start_time:
            raise ValidationError("End time cannot be before start time")
            
        # Calculate actual duration if start and end times are set
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds() / 60
            if not self.actual_duration_minutes or abs(self.actual_duration_minutes - duration) > 1:
                self.actual_duration_minutes = int(duration)

    def update_status(self, new_status, user=None):
        """
        Update the process status with proper time tracking.
        
        Args:
            new_status: The new status to set
            user: The operator (optional)
            
        Returns:
            bool: True if status was updated, False otherwise
        """
        old_status = self.status
        self.status = new_status
        now = timezone.now()
        
        # Update timestamps based on status
        if new_status == 'SETUP' and old_status == 'PENDING':
            self.start_time = now
            if user:
                self.operator = user
        elif new_status == 'RUNNING' and old_status == 'SETUP':
            # Calculate setup time
            if self.start_time:
                self.setup_time_minutes = int((now - self.start_time).total_seconds() / 60)
        elif new_status == 'COMPLETED':
            self.end_time = now
            # Calculate actual duration
            if self.start_time:
                self.actual_duration_minutes = int((now - self.start_time).total_seconds() / 60)
                
        self.save()
        
        # Update sub work order completion percentage
        self._update_sub_work_order_completion()
        
        return True

    def _update_sub_work_order_completion(self):
        """
        Update the completion percentage of the parent sub work order
        based on completed processes.
        """
        total_processes = self.sub_work_order.processes.count()
        if total_processes > 0:
            completed_processes = self.sub_work_order.processes.filter(
                status='COMPLETED'
            ).count()
            completion = (completed_processes / total_processes) * 100
            self.sub_work_order.completion_percentage = completion
            self.sub_work_order.save(update_fields=['completion_percentage'])

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Process {self.sequence_order} for {self.sub_work_order}"

class WorkOrderOutput(BaseModel):
    """
    Records the output of work orders and manages inventory categorization.
    """
    OUTPUT_STATUS = [
        ('GOOD', 'Good Quality'),
        ('REWORK', 'Needs Rework'),
        ('SCRAP', 'Scrap'),
        ('QUARANTINE', 'In Quarantine')
    ]

    sub_work_order = models.ForeignKey(SubWorkOrder, on_delete=models.PROTECT, related_name='outputs')
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=OUTPUT_STATUS)
    target_category = models.ForeignKey('inventory.InventoryCategory', on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True)
    quarantine_reason = models.TextField(blank=True, null=True, help_text="Reason for quarantine status if applicable")
    inspection_required = models.BooleanField(default=False, help_text="Whether quality inspection is required")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_outputs')
    production_date = models.DateField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sub_work_order']),
            models.Index(fields=['target_category']),
            models.Index(fields=['inspection_required']),
            models.Index(fields=['production_date']),
        ]

    def clean(self):
        super().clean()
        
        # Validate total output doesn't exceed work order quantity
        total_output = WorkOrderOutput.objects.filter(
            sub_work_order=self.sub_work_order
        ).exclude(
            pk=self.pk
        ).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        if total_output + self.quantity > self.sub_work_order.quantity:
            raise ValidationError(
                f"Total output quantity ({total_output + self.quantity}) cannot exceed work order quantity ({self.sub_work_order.quantity})"
            )
        
        # Validate quarantine reason is provided when status is QUARANTINE
        if self.status == 'QUARANTINE' and not self.quarantine_reason:
            raise ValidationError("Quarantine reason is required for items in quarantine status")
        
        # Set inspection required based on status
        self.inspection_required = self.status in ['REWORK', 'QUARANTINE']
        
        # Validate target category based on status
        if self.status == 'GOOD':
            # Target category validation will be handled in the model's clean method
            pass
        elif self.status == 'REWORK' and self.target_category.name != 'KARANTINA':
            raise ValidationError("Items needing rework must go to Karantina")
        elif self.status == 'SCRAP' and self.target_category.name != 'HURDA':
            raise ValidationError("Scrap items must go to Hurda")
        elif self.status == 'QUARANTINE' and self.target_category.name != 'KARANTINA':
            raise ValidationError("Quarantined items must go to Karantina category")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update sub work order quantities
        if self.status == 'SCRAP':
            self.sub_work_order.scrap_quantity = WorkOrderOutput.objects.filter(
                sub_work_order=self.sub_work_order,
                status='SCRAP'
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        self.sub_work_order.output_quantity = WorkOrderOutput.objects.filter(
            sub_work_order=self.sub_work_order,
            status__in=['GOOD', 'REWORK', 'SCRAP']
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        self.sub_work_order.save()
        
        # If all expected quantity is produced, mark the sub work order as completed
        if self.sub_work_order.output_quantity >= self.sub_work_order.quantity:
            try:
                self.sub_work_order.update_status(WorkOrderStatus.COMPLETED)
            except ValidationError:
                # Log but continue
                pass

    def __str__(self):
        status_str = self.get_status_display()
        if self.status == 'QUARANTINE':
            truncated = self.quarantine_reason[:30] + "..." if len(self.quarantine_reason or "") > 30 else self.quarantine_reason
            status_str += f" (Reason: {truncated})"
        return f"{self.sub_work_order} - {self.quantity} units - {status_str}" 