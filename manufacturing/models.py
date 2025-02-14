from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer, ProductType, ComponentType, MachineStatus, WorkOrderStatus
from sales.models import SalesOrderItem
from datetime import datetime, timedelta

class MachineType(models.TextChoices):
    MILLING = 'MILLING', 'Milling Machine'
    LATHE = 'LATHE', 'Lathe Machine'
    DRILL = 'DRILL', 'Drill Press'
    GRINDING = 'GRINDING', 'Grinding Machine'

class Machine(BaseModel):
    machine_code = models.CharField(max_length=50, unique=True)
    machine_type = models.CharField(max_length=50, choices=MachineType.choices)
    brand = models.CharField(max_length=50, blank=True, null=True)
    model = models.CharField(max_length=50, blank=True, null=True)
    axis_count = models.IntegerField(blank=True, null=True)
    internal_cooling = models.BooleanField(default=False)
    motor_power_kva = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    holder_type = models.CharField(max_length=50, blank=True, null=True)
    spindle_motor_power_10_percent_kw = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    spindle_motor_power_30_percent_kw = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    power_hp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    spindle_speed_rpm = models.IntegerField(blank=True, null=True)
    tool_count = models.IntegerField(blank=True, null=True)
    nc_control_unit = models.CharField(max_length=50, blank=True, null=True)
    manufacturing_year = models.IntegerField(blank=True, null=True)
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

    def __str__(self):
        return f"{self.process_code} - {self.process_name}"

class BOMProcessConfig(models.Model):
    process = models.ForeignKey(ManufacturingProcess, on_delete=models.PROTECT)
    machine_type = models.CharField(max_length=50)
    estimated_duration_minutes = models.IntegerField()
    tooling_requirements = models.JSONField(blank=True, null=True)
    quality_checks = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "BOM Process Configuration"
        verbose_name_plural = "BOM Process Configurations"

    def __str__(self):
        return f"{self.process.process_code} - {self.machine_type}"

class BOM(BaseModel):
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bill of Materials"
        verbose_name_plural = "Bills of Materials"
        unique_together = ['product', 'version']
        indexes = [
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.product.product_code} - v{self.version}"

class BOMComponent(models.Model):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='components')
    component_type = models.CharField(max_length=30, choices=ComponentType.choices)
    semi_product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='semi_components'
    )
    raw_material = models.ForeignKey(
        'inventory.RawMaterial',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='material_components'
    )
    process_config = models.ForeignKey(BOMProcessConfig, on_delete=models.PROTECT, null=True, blank=True)
    standard_part = models.ForeignKey(
        'inventory.Product',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='standard_components',
        limit_choices_to={'product_type': ProductType.STANDARD_PART}
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    sequence_order = models.IntegerField()

    class Meta:
        verbose_name = "BOM Component"
        verbose_name_plural = "BOM Components"
        ordering = ['sequence_order']

    def clean(self):
        # Validate that only one of semi_product, raw_material, or process_config is set
        fields = [
            (self.semi_product, ComponentType.SEMI_PRODUCT),
            (self.raw_material, ComponentType.RAW_MATERIAL),
            (self.process_config, ComponentType.MANUFACTURING_PROCESS),
            (self.standard_part, ComponentType.STANDARD_PART),

        ]

        if self.component_type == ComponentType.STANDARD_PART:
            if self.semi_product.product_type != ProductType.STANDARD_PART:
                raise ValidationError("Standard Part components must reference Standard Part products")
        
        # Check if the set field matches the component type
        for field, expected_type in fields:
            if field and self.component_type != expected_type:
                raise ValidationError(f"Component type {self.component_type} does not match the provided field type {expected_type}")
        
        # Check if exactly one field is set
        set_fields = sum(1 for field, _ in fields if field is not None)
        if set_fields != 1:
            raise ValidationError("Exactly one of semi_product, raw_material, or process_config must be set")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.semi_product:
            return f"Semi-Product: {self.semi_product.product_code}"
        elif self.raw_material:
            return f"Raw Material: {self.raw_material.material_code}"
        else:
            return f"Process: {self.process_config.process.process_code}"

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

    def __str__(self):
        return f"{self.order_number} - {self.bom.product.product_code}"

class SubWorkOrder(BaseModel):
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

    def clean(self):
        if self.output_quantity and self.output_quantity + self.scrap_quantity > self.quantity:
            raise ValidationError("Output quantity plus scrap cannot exceed input quantity")
        
        if self.status == WorkOrderStatus.COMPLETED and not self.output_quantity:
            raise ValidationError("Output quantity must be set when completing a work order")

    def __str__(self):
        return f"{self.parent_work_order.order_number} - {self.bom_component}"

class SubWorkOrderProcess(models.Model):
    sub_work_order = models.ForeignKey(SubWorkOrder, on_delete=models.CASCADE, related_name='processes')
    process = models.ForeignKey(ManufacturingProcess, on_delete=models.PROTECT)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    sequence_order = models.IntegerField()
    planned_duration_minutes = models.IntegerField()
    actual_duration_minutes = models.IntegerField(null=True, blank=True)

    def clean(self):
        if self.machine.machine_type != self.process.machine_type:
            raise ValidationError("Machine type does not match process requirements")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sub_work_order} - {self.process.process_code}"

    class Meta:
        ordering = ['sequence_order']

class WorkOrderOutput(BaseModel):
    """
    Records the output of work orders and manages inventory categorization
    """
    OUTPUT_STATUS = [
        ('GOOD', 'Good Quality'),
        ('REWORK', 'Needs Rework'),
        ('SCRAP', 'Scrap')
    ]

    sub_work_order = models.ForeignKey(SubWorkOrder, on_delete=models.PROTECT, related_name='outputs')
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=OUTPUT_STATUS)
    target_category = models.ForeignKey('inventory.InventoryCategory', on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True)

    def clean(self):
        # Validate target category based on output status
        if self.status == 'GOOD' and self.target_category.name not in ['MAMUL', 'PROSES']:
            raise ValidationError("Good quality items must go to Mamul or Proses")
        elif self.status == 'REWORK' and self.target_category.name != 'KARANTINA':
            raise ValidationError("Items needing rework must go to Karantina")
        elif self.status == 'SCRAP' and self.target_category.name != 'HURDA':
            raise ValidationError("Scrap items must go to Hurda")

        # Validate total output doesn't exceed sub work order quantity
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
            sub_work_order=self.sub_work_order
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        self.sub_work_order.save()

    def __str__(self):
        return f"{self.sub_work_order} - {self.quantity} units - {self.status}" 