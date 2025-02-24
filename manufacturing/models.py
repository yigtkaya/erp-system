from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer, ProductType, ComponentType, MachineStatus, WorkOrderStatus
from sales.models import SalesOrderItem
from datetime import datetime, timedelta
from django.db.models import Q
from django.db.models.query import QuerySet
from model_utils.managers import InheritanceManager

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
            models.Index(fields=['machine_type']),
        ]

    def __str__(self):
        return f"{self.process_code} - {self.process_name}"

class BOMProcessConfig(models.Model):
    process = models.ForeignKey(ManufacturingProcess, on_delete=models.PROTECT)
    axis_count = models.CharField(
        max_length=20,
        choices=AxisCount.choices,
        help_text="Required machine axis count for this process configuration",
        blank=True,
        null=True
    )
    estimated_duration_minutes = models.IntegerField(blank=True, null=True)
    tooling_requirements = models.JSONField(blank=True, null=True)
    quality_checks = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "BOM Process Configuration"
        verbose_name_plural = "BOM Process Configurations"
        indexes = [
            models.Index(fields=['process']),
            models.Index(fields=['axis_count']),
        ]

    def __str__(self):
        axis_str = f" - {self.axis_count}" if self.axis_count else ""
        return f"{self.process.process_code}{axis_str}"

class BOM(BaseModel):
    """
    The BOM is associated with a product that is manufactured.
    
    • Standard products (bought externally) are not allowed a BOM.
    • For Montaged products the BOM can only have ProductComponents (assembly of semis/standards).
    • For Semi and Single products the BOM is based on a raw material process (ProcessComponents) and may include a product component if a purchased (Standard) part is used.
    """
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        to_field='product_code'
    )
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bill of Materials"
        verbose_name_plural = "Bills of Materials"
        unique_together = ['product', 'version']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['is_active']),
        ]

    def clean(self):
        super().clean()
        # Disallow BOM for externally purchased Standard products.
        if self.product.product_type == ProductType.STANDARD_PART:
            raise ValidationError("Standard products (bought externally) cannot have a BOM")
        
        # Validate components based on the parent product type
        # Remove the self.pk check to ensure validation runs during creation as well
        if hasattr(self, 'components'):
            # Use the InheritanceManager helper to separate component types
            product_components = self.components.instance_of(ProductComponent)
            process_components = self.components.instance_of(ProcessComponent)
            
            if self.product.product_type == ProductType.MONTAGED:
                # Montaged BOMs may only contain product components.
                if process_components.exists():
                    raise ValidationError("Montaged products cannot have process components")
                # In a montaged BOM, each product component must reference either a Semi or a Standard product.
                for pc in product_components:
                    if pc.product.product_type not in [ProductType.SEMI, ProductType.STANDARD_PART]:
                        raise ValidationError("Montaged products can only contain Semi or Standard products as components")
            elif self.product.product_type in [ProductType.SEMI, ProductType.SINGLE]:
                # For Semi and Single products, process components are required to define the raw material process.
                # If a product component is used, it must reference a Standard product.
                for pc in product_components:
                    if pc.product.product_type != ProductType.STANDARD_PART:
                        raise ValidationError("For Semi/Single products, product components must be Standard (purchased) parts")
    
    def __str__(self):
        return f"{self.product.product_code} - v{self.version}"

class BOMComponent(BaseModel):
    """
    A generic BOM component that is extended by:
      • ProductComponent – for including an existing product (assembly/sub-assembly)
      • ProcessComponent – for specifying a manufacturing process step using raw materials.
    """
    COMPONENT_TYPES = [
        ('PRODUCT', 'Product Component'),
        ('PROCESS', 'Process Component'),
    ]

    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='components')
    sequence_order = models.IntegerField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    component_type = models.CharField(
        max_length=20,
        choices=COMPONENT_TYPES,
        default='PRODUCT',
        editable=False
    )

    objects = InheritanceManager()

    class Meta:
        ordering = ['sequence_order']
        unique_together = [('bom', 'sequence_order')]
        indexes = [
            models.Index(fields=['bom']),
            models.Index(fields=['component_type']),
        ]

    def clean(self):
        super().clean()
        # Check for duplicate sequence_order within the same BOM
        if self.bom_id is not None and self.sequence_order is not None:
            # Exclude self when checking for duplicates (important for updates)
            duplicate_exists = BOMComponent.objects.filter(
                bom=self.bom,
                sequence_order=self.sequence_order
            ).exclude(pk=self.pk).exists()
            
            if duplicate_exists:
                raise ValidationError({
                    'sequence_order': f'A component with sequence order {self.sequence_order} already exists in this BOM.'
                })

    def save(self, *args, **kwargs):
        # Set component_type based on the actual class
        if isinstance(self, ProductComponent):
            self.component_type = 'PRODUCT'
            # Ensure quantity is required for ProductComponent
            if self.quantity is None:
                raise ValidationError("Quantity is required for product components")
        elif isinstance(self, ProcessComponent):
            self.component_type = 'PROCESS'
        self.clean()  # Run validation before saving
        super().save(*args, **kwargs)

    def __str__(self):
        quantity_str = f" (x{self.quantity})" if self.quantity is not None else ""
        return f"Component {self.sequence_order} of {self.bom}{quantity_str}"

class ProductComponent(BOMComponent):
    """
    This component indicates that the BOM uses another product.
    
    • For Montaged products, the referenced product must be either a Semi (sub–assembly)
      or a Standard (purchased) part.
    • For Semi and Single product BOMs, if a product component is used it must reference a Standard product.
    """
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT)

    def clean(self):
        super().clean()
        if self.bom.product == self.product:
            raise ValidationError("A product cannot be a component of itself")
        
        # Check for circular dependencies
        self._check_circular_dependency(self.bom.product, [self.product])
        
        parent_type = self.bom.product.product_type
        if parent_type == ProductType.MONTAGED:
            if self.product.product_type not in [ProductType.SEMI, ProductType.STANDARD_PART]:
                raise ValidationError("Montaged products can only contain Semi or Standard products as components")
        elif parent_type in [ProductType.SEMI, ProductType.SINGLE]:
            if self.product.product_type != ProductType.STANDARD_PART:
                raise ValidationError("Semi and Single products can only include Standard parts as product components")

    def _check_circular_dependency(self, parent_product, visited_products):
        """
        Recursively check for circular dependencies in the BOM structure.
        
        Args:
            parent_product: The product to check components for
            visited_products: List of products already visited in this branch
        """
        # Get all BOMs for the parent product
        boms = BOM.objects.filter(product=parent_product, is_active=True)
        
        for bom in boms:
            # Get all product components in this BOM
            product_components = ProductComponent.objects.filter(bom=bom)
            
            for component in product_components:
                if component.product in visited_products:
                    raise ValidationError(f"Circular dependency detected: {component.product} is already used in the BOM hierarchy")
                
                # Only recurse for Semi products (Standard products don't have BOMs)
                if component.product.product_type == ProductType.SEMI:
                    self._check_circular_dependency(component.product, visited_products + [component.product])

    def __str__(self):
        return f"{self.product.product_code} (x{self.quantity})"

class ProcessComponent(BOMComponent):
    """
    This component represents a manufacturing process step where raw materials are transformed.
    
    • Only Semi or Single products may include process components.
    """
    process_config = models.ForeignKey(BOMProcessConfig, on_delete=models.PROTECT)
    raw_material = models.ForeignKey('inventory.RawMaterial', on_delete=models.PROTECT, null=True, blank=True)
    
    def clean(self):
        super().clean()
        if self.bom.product.product_type not in [ProductType.SEMI, ProductType.SINGLE]:
            raise ValidationError("Only Semi or Single products can have process components")

    def __str__(self):
        return f"{self.process_config.process.process_code} (x{self.quantity})"


class WorkOrder(BaseModel):
    order_number = models.CharField(max_length=50, unique=True)
    sales_order_item = models.ForeignKey(SalesOrderItem, on_delete=models.PROTECT)
    bom = models.ForeignKey(BOM, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    planned_start = models.DateField()
    planned_end = models.DateField()
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)
    priority = models.IntegerField(default=1)  # 1 is highest priority
    notes = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.order_number} - {self.bom.product.product_code}"

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
    actual_start = models.DateField(null=True, blank=True)
    actual_end = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=WorkOrderStatus.choices, default=WorkOrderStatus.PLANNED)
    output_quantity = models.IntegerField(null=True, blank=True)
    scrap_quantity = models.IntegerField(default=0)
    target_category = models.ForeignKey('inventory.InventoryCategory', on_delete=models.PROTECT, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['parent_work_order']),
        ]

    @property
    def component_type(self):
        """Returns the specific type of BOM component (Process or Product)"""
        return self.bom_component.get_real_instance_class().__name__

    @property
    def is_process_component(self):
        """Check if this sub work order is for a process component"""
        return isinstance(self.bom_component.get_real_instance(), ProcessComponent)

    @property
    def is_product_component(self):
        """Check if this sub work order is for a product component"""
        return isinstance(self.bom_component.get_real_instance(), ProductComponent)

    def get_specific_component(self):
        """Get the actual ProcessComponent or ProductComponent instance"""
        return self.bom_component.get_real_instance()

    def clean(self):
        super().clean()
        if self.output_quantity and self.output_quantity + self.scrap_quantity > self.quantity:
            raise ValidationError("Output quantity plus scrap cannot exceed input quantity")
        
        if self.status == WorkOrderStatus.COMPLETED and not self.output_quantity:
            raise ValidationError("Output quantity must be set when completing a work order")

        # Validate target category based on component type
        if self.target_category:
            specific_component = self.get_specific_component()
            if isinstance(specific_component, ProcessComponent):
                # For Semi or Single products using process components the finished goods
                # (raw processed items) should go to the 'PROSES' category.
                if specific_component.bom.product.product_type in [ProductType.SEMI, ProductType.SINGLE]:
                    if self.target_category.name != 'PROSES':
                        raise ValidationError("Processed Semi/Single products must target Proses category")
            elif isinstance(specific_component, ProductComponent):
                # For Montaged product BOMs the product components (usually Semi sub–assemblies)
                # should target the 'MAMUL' category.
                if specific_component.bom.product.product_type == ProductType.MONTAGED:
                    if self.target_category.name != 'MAMUL':
                        raise ValidationError("Montaged product components must target Mamul category")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        component = self.get_specific_component()
        if isinstance(component, ProcessComponent):
            return f"{self.parent_work_order.order_number} - Process: {component.process_config.process.process_code}"
        else:
            return f"{self.parent_work_order.order_number} - Product: {component.product.product_code}"

class SubWorkOrderProcess(models.Model):
    """
    For sub work orders based on a process component, you can track the individual process steps.
    """
    sub_work_order = models.ForeignKey(SubWorkOrder, on_delete=models.CASCADE, related_name='processes')
    process = models.ForeignKey(ManufacturingProcess, on_delete=models.PROTECT)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    sequence_order = models.IntegerField()
    planned_duration_minutes = models.IntegerField(null=True, blank=True)
    actual_duration_minutes = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['sequence_order']
        indexes = [
            models.Index(fields=['sub_work_order']),
            models.Index(fields=['machine']),
        ]

    def clean(self):
        super().clean()
        # Ensure the sub work order is for a process component
        if not self.sub_work_order.is_process_component:
            raise ValidationError("Can only add processes to sub work orders with process components")
        process_component = self.sub_work_order.get_specific_component()
        # Validate machine requirements against the process configuration.
        if process_component.process_config.axis_count and self.machine.axis_count != process_component.process_config.axis_count:
            raise ValidationError("Machine axis count does not match process requirements")
        if self.machine.machine_type != process_component.process_config.process.machine_type:
            raise ValidationError("Machine type does not match process requirements")
        if self.process != process_component.process_config.process:
            raise ValidationError("Process must match the one specified in the BOM process configuration")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sub_work_order} - {self.process.process_code}"

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

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sub_work_order']),
            models.Index(fields=['target_category']),
            models.Index(fields=['inspection_required']),
        ]

    def clean(self):
        super().clean()
        component = self.sub_work_order.get_specific_component()
        
        # Validate target category based on output status and component type
        if self.status == 'GOOD':
            if isinstance(component, ProcessComponent):
                if component.bom.product.product_type in [ProductType.SEMI, ProductType.SINGLE]:
                    if self.target_category.name != 'PROSES':
                        raise ValidationError("Good quality processed Semi/Single products must go to Proses category")
            elif isinstance(component, ProductComponent):
                if component.bom.product.product_type == ProductType.MONTAGED:
                    if self.target_category.name != 'MAMUL':
                        raise ValidationError("Good quality Montaged products must go to Mamul category")
        elif self.status == 'REWORK':
            if self.target_category.name != 'KARANTINA':
                raise ValidationError("Items needing rework must go to Karantina")
        elif self.status == 'SCRAP':
            if self.target_category.name != 'HURDA':
                raise ValidationError("Scrap items must go to Hurda")
        elif self.status == 'QUARANTINE':
            if self.target_category.name != 'KARANTINA':
                raise ValidationError("Quarantined items must go to Karantina category")
            if not self.quarantine_reason:
                raise ValidationError("Quarantine reason is required for items in quarantine status")
            self.inspection_required = True

        total_output = WorkOrderOutput.objects.filter(sub_work_order=self.sub_work_order).exclude(pk=self.pk).aggregate(
            total=models.Sum('quantity'))['total'] or 0
        
        if total_output + self.quantity > self.sub_work_order.quantity:
            raise ValidationError("Total output quantity cannot exceed work order quantity")

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

    def __str__(self):
        status_str = self.get_status_display()
        if self.status == 'QUARANTINE':
            truncated = self.quarantine_reason[:30] + "..." if len(self.quarantine_reason or "") > 30 else self.quarantine_reason
            status_str += f" (Reason: {truncated})"
        return f"{self.sub_work_order} - {self.quantity} units - {status_str}" 