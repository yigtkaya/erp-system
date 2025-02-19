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
    axis_count = models.CharField(
        max_length=20,
        choices=AxisCount.choices,
        help_text="Required machine axis count for this process configuration",
        blank=True,
        null=True
    )
    estimated_duration_minutes = models.IntegerField()
    tooling_requirements = models.JSONField(blank=True, null=True)
    quality_checks = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "BOM Process Configuration"
        verbose_name_plural = "BOM Process Configurations"

    def __str__(self):
        return f"{self.process.process_code} - {self.axis_count}"

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

    def clean(self):
        super().clean()
        if self.product.product_type == ProductType.SINGLE:
            raise ValidationError("Single products cannot have a BOM")
        
        # Ensure all components are valid for the product type
        if self.pk:  # Only check if BOM already exists
            product_components = self.components.instance_of(ProductComponent)
            process_components = self.components.instance_of(ProcessComponent)
            
            if self.product.product_type == ProductType.MONTAGED and process_components.exists():
                raise ValidationError("Montaged products cannot have process components")
            
            if self.product.product_type == ProductType.SEMI and product_components.exists():
                raise ValidationError("Semi-finished products cannot have product components")

    def __str__(self):
        return f"{self.product.product_code} - v{self.version}"

class BOMComponent(BaseModel):
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name='components')
    sequence_order = models.IntegerField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    objects = InheritanceManager()

    class Meta:
        ordering = ['sequence_order']

    def __str__(self):
        return f"Component {self.sequence_order} of {self.bom}"

class ProductComponent(BOMComponent):
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT)

    def clean(self):
        super().clean()
        if self.bom.product == self.product:
            raise ValidationError("A product cannot be a component of itself")
        
        # Validate based on parent BOM's product type
        parent_type = self.bom.product.product_type
        if parent_type == ProductType.MONTAGED:
            if self.product.product_type not in [ProductType.MONTAGED, ProductType.SEMI, ProductType.STANDARD_PART]:
                raise ValidationError("Montaged products can only contain other montaged products, semi-finished products, or standard parts")
        elif parent_type == ProductType.SEMI:
            raise ValidationError("Semi-finished products cannot contain other products as components")

    def __str__(self):
        return f"{self.product.product_code} (x{self.quantity})"

class ProcessComponent(BOMComponent):
    process_config = models.ForeignKey(BOMProcessConfig, on_delete=models.PROTECT)
    raw_material = models.ForeignKey('inventory.RawMaterial', on_delete=models.PROTECT, null=True, blank=True)
    
    def clean(self):
        super().clean()
        if self.bom.product.product_type != ProductType.SEMI:
            raise ValidationError("Only semi-finished products can have process components")

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
        if self.machine.axis_count != self.sub_work_order.bom_component.process_config.axis_count:
            raise ValidationError("Machine axis count does not match process requirements")

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