from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer, ProductType, MaterialType
from django.core.validators import MinValueValidator, MaxValueValidator
import pathlib 
from django.db.models import Sum
from django.apps import apps
from django.conf import settings
import uuid
from simple_history.models import HistoricalRecords

class Status(models.TextChoices):
    ACTIVE = 'AKTIF', 'Aktif'
    INACTIVE = 'PASIF', 'Pasif'

class InventoryCategory(models.Model):
    CATEGORY_CHOICES = [
        ('HAMMADDE', 'Hammadde'),  # Raw Materials and Standard Parts
        ('PROSES', 'Proses'),      # Unfinished/Semi Products
        ('MAMUL', 'Mamül'),        # Finished and Single Products
        ('KARANTINA', 'Karantina'), # Items needing decision
        ('HURDA', 'Hurda'),        # Scrap items
        ('TAKIMHANE', 'Takımhane') # Tool storage
    ]

    name = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Inventory Category"
        verbose_name_plural = "Inventory Categories"

    def __str__(self):
        return self.get_name_display()

class UnitOfMeasure(models.Model):
    unit_code = models.CharField(max_length=10, unique=True)
    unit_name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Unit of Measure"
        verbose_name_plural = "Units of Measure"

    def __str__(self):
        return f"{self.unit_code} - {self.unit_name}"

class Product(BaseModel):
    product_code = models.CharField(max_length=50, unique=True)
    product_name = models.CharField(max_length=100)
    project_name = models.CharField(max_length=100, null=True, blank=True)
    product_type = models.CharField(max_length=20, choices=ProductType.choices)
    multicode = models.IntegerField(
        null=True, 
        blank=True,
        validators=[
            MinValueValidator(-2147483648),
            MaxValueValidator(2147483647)
        ]
    )
    description = models.TextField(blank=True, null=True)
    current_stock = models.IntegerField(default=0)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)
    inventory_category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['product_code']

    def clean(self):
        if self.product_type == ProductType.SINGLE and self.customer:
            raise ValidationError("Single parts shouldn't be customer-specific")
        
        # Validate inventory category based on product type
        if self.product_type == ProductType.SINGLE and self.inventory_category.name not in ['HAMMADDE', 'HURDA', 'KARANTINA']:
            raise ValidationError("Single parts can only be in Hammadde, Hurda, or Karantina categories")
        elif self.product_type == ProductType.SEMI and self.inventory_category.name not in ['PROSES', 'MAMUL', 'KARANTINA', 'HURDA']:
            raise ValidationError("Semi-finished products can only be in Proses, Mamul, Karantina, or Hurda categories")
        elif self.product_type == ProductType.MONTAGED and self.inventory_category.name not in ['MAMUL', 'KARANTINA', 'HURDA']:
            raise ValidationError("Montaged products can only be in Mamul, Karantina, or Hurda categories")
        elif self.product_type == ProductType.STANDARD_PART and self.inventory_category.name not in ['HAMMADDE', 'HURDA', 'KARANTINA']:
            raise ValidationError("Standard parts can only be in Hammadde, Hurda, or Karantina categories")
    
    def __str__(self):
        return f"{self.product_code} - {self.product_name}"

    @property
    def in_process_quantity_by_process(self):
        """
        Returns a dictionary mapping each manufacturing process to the pending quantity
        for this semi-finished product. It computes the pending amount from each sub work order,
        grouping by the process code from the BOM component's process configuration.
        """
        if self.product_type != 'SEMI':
            return {}

        result = {}

        # Get BOM components where this product is used as a semi-finished product
        components = apps.get_model('manufacturing', 'BOMComponent').objects.filter(
            bom__product=self,
            bom__product__product_type__in=['SEMI', 'SINGLE']
        )

        # Get in-progress work orders related to these components
        work_orders = apps.get_model('manufacturing', 'WorkOrder').objects.filter(
            bom__components__in=components, status='IN_PROGRESS'
        ).distinct()

        for work_order in work_orders:
            # We assume the reverse relation from WorkOrder to SubWorkOrder is named 'sub_orders'
            sub_work_orders = work_order.sub_orders.filter(
                bom_component__in=components
            )
            for sub_order in sub_work_orders:
                process_component = sub_order.get_specific_component()
                process_config = process_component.process_config
                # Use the process code from the manufacturing process if available
                process_name = (
                    process_config.process.process_code
                    if process_config and hasattr(process_config, 'process')
                    else 'Unknown Process'
                )
                scheduled_qty = sub_order.quantity  # planned quantity for this sub work order
                completed_qty = apps.get_model('manufacturing', 'WorkOrderOutput').objects.filter(
                    sub_work_order=sub_order, status='GOOD'
                ).aggregate(total=Sum('quantity'))['total'] or 0
                pending_qty = scheduled_qty - completed_qty

                if pending_qty > 0:
                    result[process_name] = result.get(process_name, 0) + pending_qty

        return result

class TechnicalDrawing(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    version = models.CharField(max_length=20)
    drawing_code = models.CharField(max_length=50)
    drawing_file = models.FileField(
        upload_to='technical_drawings/%Y/%m/%d/', 
        max_length=500, 
        blank=True, 
        null=True,
        storage=settings.DEFAULT_FILE_STORAGE if hasattr(settings, 'USE_CLOUDFLARE_R2') and settings.USE_CLOUDFLARE_R2 else None
    )
    effective_date = models.DateField()
    is_current = models.BooleanField(default=True)
    revision_notes = models.CharField(max_length=500, blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_drawings')
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Technical Drawing"
        verbose_name_plural = "Technical Drawings"
        unique_together = ['product', 'version']
        indexes = [
            models.Index(fields=['product', 'is_current']),
        ]

    def clean(self):
        # Ensure only one current version exists per product
        if self.is_current:
            current_drawings = TechnicalDrawing.objects.filter(
                product=self.product,
                is_current=True
            ).exclude(pk=self.pk)
            if current_drawings.exists():
                # Set all other versions to not current
                current_drawings.update(is_current=False)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.drawing_code} v{self.version}"
    
    @property
    def drawing_url(self):
        """
        Returns the URL for the drawing file, using Cloudflare R2 if enabled.
        """
        if self.drawing_file:
            return self.drawing_file.url
        return None

class RawMaterial(BaseModel):
    material_code = models.CharField(max_length=50, unique=True)
    material_name = models.CharField(max_length=100)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    inventory_category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT, null=True, blank=True)
    
    # New field for material type with enum-like choices
    material_type = models.CharField(max_length=10, choices=MaterialType.choices, default=MaterialType.STEEL)
    
    # New fields for dimensions / measurements
    width = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    height = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    thickness = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    diameter_mm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])

    class Meta:
        verbose_name = "Raw Material"
        verbose_name_plural = "Raw Materials"

    def clean(self):
        if self.inventory_category and self.inventory_category.name not in ['HAMMADDE', 'HURDA', 'KARANTINA']:
            raise ValidationError("Raw materials can only be in Hammadde, Hurda, or Karantina categories")
        # Optional: Additional validations for the new fields can be added here.

    def __str__(self):
        return f"{self.material_code} - {self.material_name}"

    def get_process_components(self):
        """Get all process components that use this raw material."""
        components = apps.get_model('manufacturing', 'BOMComponent').objects.filter(
            material=self,
            bom__product__product_type__in=['SEMI', 'SINGLE']
        )
        return components

class InventoryTransaction(BaseModel):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
        ('RETURN', 'Return'),
        ('TRANSFER', 'Category Transfer'),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT, null=True, blank=True)
    quantity_change = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions_performed')
    verified_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='transactions_verified')
    notes = models.TextField(blank=True, null=True)
    from_category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT, related_name='transactions_from', null=True, blank=True)
    to_category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT, related_name='transactions_to', null=True, blank=True)
    reference_id = models.CharField(max_length=50, null=True, blank=True)

    def clean(self):
        if not bool(self.product) != bool(self.material):
            raise ValidationError("Either product or material must be set, but not both.")
        
        if self.transaction_type == 'TRANSFER':
            if not self.from_category or not self.to_category:
                raise ValidationError("Category transfer requires both from and to categories")
            
            if self.product and self.to_category.name not in self._get_allowed_categories(self.product.product_type):
                raise ValidationError(f"Invalid category transfer for product type {self.product.product_type}")
            
            if self.material and self.to_category.name not in ['HAMMADDE', 'HURDA', 'KARANTINA']:
                raise ValidationError("Invalid category transfer for raw material")

    def _get_allowed_categories(self, product_type):
        if product_type == ProductType.SINGLE:
            return ['HAMMADDE', 'HURDA', 'KARANTINA']
        elif product_type == ProductType.SEMI:
            return ['PROSES', 'MAMUL', 'KARANTINA', 'HURDA']
        else:  # MONTAGED
            return ['MAMUL', 'KARANTINA', 'HURDA']

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update stock levels and categories
        if self.transaction_type != 'RESERVATION':
            if self.product:
                if self.transaction_type == 'TRANSFER':
                    self.product.inventory_category = self.to_category
                self.product.current_stock += self.quantity_change
                self.product.save()
            elif self.material:
                if self.transaction_type == 'TRANSFER':
                    self.material.inventory_category = self.to_category
                self.material.current_stock += self.quantity_change
                self.material.save()

    def __str__(self):
        item = self.product or self.material
        return f"{self.transaction_type} - {item} - {self.quantity_change}"

    class Meta:
        verbose_name = "Inventory Transaction"
        verbose_name_plural = "Inventory Transactions"
        indexes = [
            models.Index(fields=['reference_id', 'transaction_type']),
        ]

class ToolHolderStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    IN_USE = 'IN_USE', 'In Use'
    DAMAGED = 'DAMAGED', 'Damaged'
    UNDER_MAINTENANCE = 'UNDER_MAINTENANCE', 'Under Maintenance'
    RETIRED = 'RETIRED', 'Retired'

class Tool(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_code = models.CharField(max_length=50, unique=True, db_index=True)
    supplier_name = models.CharField(max_length=100)
    product_code = models.CharField(max_length=50)
    unit_price_tl = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price_euro = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    tool_insert_code = models.CharField(max_length=100)
    tool_material = models.CharField(max_length=100)
    tool_diameter = models.DecimalField(max_digits=10, decimal_places=2)
    tool_length = models.DecimalField(max_digits=10, decimal_places=2)
    tool_width = models.DecimalField(max_digits=10, decimal_places=2)
    tool_height = models.DecimalField(max_digits=10, decimal_places=2)
    tool_angle = models.DecimalField(max_digits=10, decimal_places=2)
    tool_radius = models.DecimalField(max_digits=10, decimal_places=2)
    tool_connection_diameter = models.DecimalField(max_digits=10, decimal_places=2)
    tool_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=ToolHolderStatus.choices, default=ToolHolderStatus.AVAILABLE)
    row = models.IntegerField()
    column = models.IntegerField()
    table_id = models.UUIDField()
    description = models.TextField(null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Tool"
        verbose_name_plural = "Tools"
        indexes = [
            models.Index(fields=['tool_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.stock_code} - {self.supplier_name}"

class Holder(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_code = models.CharField(max_length=50, unique=True, db_index=True)
    supplier_name = models.CharField(max_length=100)
    product_code = models.CharField(max_length=50)
    unit_price_tl = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price_euro = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price_usd = models.DecimalField(max_digits=10, decimal_places=2)
    holder_type = models.CharField(max_length=50)
    pulley_type = models.CharField(max_length=50)
    water_cooling = models.BooleanField(default=False)
    distance_cooling = models.BooleanField(default=False)
    tool_connection_diameter = models.DecimalField(max_digits=10, decimal_places=2)
    holder_type_enum = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=ToolHolderStatus.choices, default=ToolHolderStatus.AVAILABLE)
    row = models.IntegerField()
    column = models.IntegerField()
    table_id = models.UUIDField()
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Holder"
        verbose_name_plural = "Holders"
        indexes = [
            models.Index(fields=['holder_type']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.stock_code} - {self.supplier_name}"

class Fixture(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        verbose_name = "Fixture"
        verbose_name_plural = "Fixtures"
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name or 'No Name'}"

class ControlGauge(BaseModel):
    GAUGE_STATUS_CHOICES = [
        ('UYGUN', 'Uygun'),
        ('KULLANILMIYOR', 'Kullanılmıyor'),
        ('HURDA', 'Hurda'),
        ('KAYIP', 'Kayıp'),
        ('BAKIMDA', 'Bakımda'),
        ('KALIBRASYONDA', 'Kalibrasyonda'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_code = models.CharField(max_length=50, unique=True, db_index=True)
    stock_name = models.CharField(max_length=100)
    stock_type = models.CharField(max_length=50, null=True, blank=True)
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    measuring_range = models.CharField(max_length=100, null=True, blank=True)
    resolution = models.CharField(max_length=50, null=True, blank=True)
    calibration_made_by = models.CharField(max_length=100, null=True, blank=True)
    calibration_date = models.DateField(null=True, blank=True)
    calibration_per_year = models.CharField(max_length=50, default='1 / Yıl')
    upcoming_calibration_date = models.DateField(null=True, blank=True)
    certificate_no = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=20, choices=GAUGE_STATUS_CHOICES, default='KULLANILMIYOR')
    current_location = models.CharField(max_length=100, null=True, blank=True)
    scrap_lost_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Control Gauge"
        verbose_name_plural = "Control Gauges"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['upcoming_calibration_date']),
        ]

    def __str__(self):
        return f"{self.stock_code} - {self.stock_name}"

