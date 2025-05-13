# inventory/models.py
from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseModel, Customer
from common.models import FileVersionManager, ContentType
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator
from django.apps import apps
import re


class ProductType(models.TextChoices):
    MONTAGED = 'MONTAGED', 'Montaged'
    SEMI = 'SEMI', 'Semi'
    SINGLE = 'SINGLE', 'Single'
    STANDARD_PART = 'STANDARD_PART', 'Standard Part'


class MaterialType(models.TextChoices):
    STEEL = 'STEEL', 'Steel'
    ALUMINUM = 'ALUMINUM', 'Aluminum'
    STAINLESS = 'STAINLESS', 'Stainless Steel'
    BRASS = 'BRASS', 'Brass'
    COPPER = 'COPPER', 'Copper'
    PLASTIC = 'PLASTIC', 'Plastic'
    OTHER = 'OTHER', 'Other'


class RawMaterial(BaseModel):
    material_code = models.CharField(max_length=50, unique=True)
    material_name = models.CharField(max_length=100)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reserved_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.ForeignKey('UnitOfMeasure', on_delete=models.PROTECT)
    inventory_category = models.ForeignKey('InventoryCategory', on_delete=models.PROTECT, null=True, blank=True)
    material_type = models.CharField(max_length=20, choices=MaterialType.choices, default=MaterialType.STEEL)
    
    # Specifications
    width = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    height = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    thickness = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    diameter_mm = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0.0)])
    weight_per_unit = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    
    # Inventory management
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    lead_time_days = models.IntegerField(null=True, blank=True)
    
    # Additional info
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    tags = models.JSONField(null=True, blank=True, help_text="List of tags for searching")

    class Meta:
        db_table = 'raw_materials'
        verbose_name = "Raw Material"
        verbose_name_plural = "Raw Materials"
        ordering = ['material_code']
        indexes = [
            models.Index(fields=['material_code']),
            models.Index(fields=['material_type']),
            models.Index(fields=['inventory_category']),
            models.Index(fields=['is_active']),
        ]

    def clean(self):
        # Validate material code format
        if not re.match(r'^[A-Za-z0-9\-\.]+$', self.material_code):
            raise ValidationError({
                'material_code': 'Material code can only contain letters, numbers, hyphens, and periods'
            })
            
        # Validate inventory category
        if self.inventory_category and self.inventory_category.name not in ['HAMMADDE', 'HURDA', 'KARANTINA']:
            raise ValidationError({
                'inventory_category': "Raw materials can only be in HAMMADDE, HURDA, or KARANTINA categories"
            })

    @property
    def available_stock(self):
        return self.current_stock - self.reserved_stock
        
    @property
    def is_below_reorder_point(self):
        if self.reorder_point is not None:
            return self.available_stock <= self.reorder_point
        return False

    def __str__(self):
        return f"{self.material_code} - {self.material_name}"
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    def get_process_components(self):
        """Get all process components that use this raw material."""
        components = apps.get_model('manufacturing', 'BOMComponent').objects.filter(
            material=self,
            bom__product__product_type__in=['SEMI', 'SINGLE']
        )
        return components
        
    # File management methods
    def get_images(self, current_only=True):
        """Get material images from file system"""
        if current_only:
            return FileVersionManager.get_current(
                content_type=ContentType.MATERIAL_IMAGE,
                object_id=str(self.id)
            )
        else:
            return FileVersionManager.get_all_versions(
                content_type=ContentType.MATERIAL_IMAGE,
                object_id=str(self.id)
            )
    
    def upload_image(self, file, notes=None, user=None):
        """Upload a material image"""
        return FileVersionManager.create_version(
            file=file,
            content_type=ContentType.MATERIAL_IMAGE,
            object_id=str(self.id),
            notes=notes,
            user=user
        )


class InventoryCategory(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'inventory_categories'
        ordering = ['name']
        
    def __str__(self):
        return self.name


class UnitOfMeasure(models.Model):
    unit_code = models.CharField(max_length=10, unique=True)
    unit_name = models.CharField(max_length=50)
    category = models.CharField(max_length=50, help_text="e.g., Length, Weight, Volume")
    
    class Meta:
        db_table = 'units_of_measure'
        ordering = ['category', 'unit_code']
    
    def __str__(self):
        return f"{self.unit_code} - {self.unit_name}"


class Product(BaseModel):
    product_code = models.CharField(max_length=50, unique=True)
    product_name = models.CharField(max_length=100)
    project_name = models.CharField(max_length=100, null=True, blank=True)
    product_type = models.CharField(max_length=20, choices=ProductType.choices)
    multicode = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    current_stock = models.IntegerField(default=0)
    reserved_stock = models.IntegerField(default=0)
    reorder_point = models.IntegerField(null=True, blank=True)
    lead_time_days = models.IntegerField(null=True, blank=True)
    unit_of_measure = models.ForeignKey('UnitOfMeasure', on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)
    inventory_category = models.ForeignKey('InventoryCategory', on_delete=models.PROTECT)
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions = models.JSONField(null=True, blank=True, help_text="Length, Width, Height in mm")
    is_active = models.BooleanField(default=True)
    tags = models.JSONField(null=True, blank=True, help_text="List of tags for searching")
    
    class Meta:
        db_table = 'products'
        ordering = ['product_code']
        indexes = [
            models.Index(fields=['product_code']),
            models.Index(fields=['product_type']),
            models.Index(fields=['inventory_category']),
            models.Index(fields=['customer']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        # Validate product code format
        if not re.match(r'^[A-Za-z0-9\-\.]+$', self.product_code):
            raise ValidationError({
                'product_code': 'Product code can only contain letters, numbers, hyphens, and periods'
            })
        
        # Validate product type and customer relationship
        if self.product_type == ProductType.SINGLE and self.customer:
            raise ValidationError({
                'customer': "Single parts shouldn't be customer-specific"
            })
        
        # Validate inventory category based on product type
        if self.inventory_category:
            self._validate_category_constraint()
    
    def _validate_category_constraint(self):
        category_name = self.inventory_category.name
        
        valid_categories = {
            ProductType.SINGLE: ['HAMMADDE', 'HURDA', 'KARANTINA'],
            ProductType.SEMI: ['PROSES', 'MAMUL', 'KARANTINA', 'HURDA'],
            ProductType.MONTAGED: ['MAMUL', 'KARANTINA', 'HURDA'],
            ProductType.STANDARD_PART: ['HAMMADDE', 'HURDA', 'KARANTINA'],
        }
        
        if self.product_type in valid_categories:
            if category_name not in valid_categories[self.product_type]:
                raise ValidationError({
                    'inventory_category': f"{self.get_product_type_display()} products can only be in {', '.join(valid_categories[self.product_type])} categories"
                })
    
    @property
    def available_stock(self):
        return self.current_stock - self.reserved_stock
    
    @property
    def is_below_reorder_point(self):
        if self.reorder_point is not None:
            return self.available_stock <= self.reorder_point
        return False
    
    def __str__(self):
        return f"{self.product_code} - {self.product_name}"
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    # File management methods
    def get_images(self, current_only=True):
        """Get product images from file system"""
        if current_only:
            return FileVersionManager.get_current(
                content_type=ContentType.PRODUCT_IMAGE,
                object_id=str(self.id)
            )
        else:
            return FileVersionManager.get_all_versions(
                content_type=ContentType.PRODUCT_IMAGE,
                object_id=str(self.id)
            )
    
    def upload_image(self, file, notes=None, user=None):
        """Upload a product image"""
        return FileVersionManager.create_version(
            file=file,
            content_type=ContentType.PRODUCT_IMAGE,
            object_id=str(self.id),
            notes=notes,
            user=user
        )


class TechnicalDrawing(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='technical_drawings')
    version = models.CharField(max_length=20)
    drawing_code = models.CharField(max_length=50)
    effective_date = models.DateField()
    is_current = models.BooleanField(default=True)
    revision_notes = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    tags = models.JSONField(null=True, blank=True, help_text="List of tags")
    
    class Meta:
        db_table = 'technical_drawings'
        unique_together = ['product', 'version']
        ordering = ['-effective_date', '-version']
        indexes = [
            models.Index(fields=['product', 'is_current']),
            models.Index(fields=['drawing_code']),
        ]
    
    def clean(self):
        # Ensure only one current version exists per product
        if self.is_current:
            current_drawings = TechnicalDrawing.objects.filter(
                product=self.product,
                is_current=True
            ).exclude(pk=self.pk)
            
            if current_drawings.exists():
                current_drawings.update(is_current=False)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.drawing_code} v{self.version}"
    
    # File management methods
    @property
    def drawing_file(self):
        """Get the current version of the drawing file from R2"""
        return FileVersionManager.get_current(
            content_type=ContentType.TECHNICAL_DRAWING,
            object_id=str(self.id)
        )
    
    @property
    def file_versions(self):
        """Get all versions of the drawing file from R2"""
        return FileVersionManager.get_all_versions(
            content_type=ContentType.TECHNICAL_DRAWING,
            object_id=str(self.id)
        )
    
    def upload_drawing(self, file, notes=None, user=None):
        """Upload a new version of the drawing to R2"""
        return FileVersionManager.create_version(
            file=file,
            content_type=ContentType.TECHNICAL_DRAWING,
            object_id=str(self.id),
            notes=notes,
            user=user
        )


class ProductBOM(BaseModel):
    parent_product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='bom_items')
    child_product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='used_in_products')
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    scrap_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    operation_sequence = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'product_bom'
        unique_together = ['parent_product', 'child_product']
        ordering = ['operation_sequence', 'child_product__product_code']
    
    def clean(self):
        if self.parent_product == self.child_product:
            raise ValidationError("A product cannot be a component of itself")
        
        # Check for circular references
        if self._creates_circular_reference():
            raise ValidationError("This would create a circular reference in the BOM")
    
    def _creates_circular_reference(self):
        """Check if adding this BOM item would create a circular reference"""
        visited = set()
        
        def check_parents(product):
            if product.id in visited:
                return True
            visited.add(product.id)
            
            # Check all products that use this product
            for bom in ProductBOM.objects.filter(child_product=product):
                if bom.parent_product == self.child_product:
                    return True
                if check_parents(bom.parent_product):
                    return True
            
            return False
        
        return check_parents(self.parent_product)
    
    def __str__(self):
        return f"{self.parent_product.product_code} -> {self.child_product.product_code} ({self.quantity})"


class ProductStock(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='stock')
    category = models.ForeignKey('InventoryCategory', on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    location = models.CharField(max_length=100, null=True, blank=True)
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    receipt_date = models.DateField(default=timezone.now)
    
    class Meta:
        db_table = 'product_stock'
        unique_together = ['product', 'category', 'batch_number']
        ordering = ['product', 'category']
        
    def __str__(self):
        return f"{self.product.product_code} - {self.category.name}: {self.quantity} {self.product.unit_of_measure}"


class StockTransactionType(models.TextChoices):
    PURCHASE_RECEIPT = 'PURCHASE_RECEIPT', 'Purchase Receipt'
    SALES_ISSUE = 'SALES_ISSUE', 'Sales Issue'
    PRODUCTION_RECEIPT = 'PRODUCTION_RECEIPT', 'Production Receipt'
    PRODUCTION_ISSUE = 'PRODUCTION_ISSUE', 'Production Issue'
    TRANSFER_IN = 'TRANSFER_IN', 'Transfer In'
    TRANSFER_OUT = 'TRANSFER_OUT', 'Transfer Out'
    RETURN_RECEIPT = 'RETURN_RECEIPT', 'Return Receipt'
    SCRAP = 'SCRAP', 'Scrap'
    ADJUSTMENT_IN = 'ADJUSTMENT_IN', 'Adjustment In'
    ADJUSTMENT_OUT = 'ADJUSTMENT_OUT', 'Adjustment Out'


# New model for stock transactions
class StockTransaction(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    raw_material = models.ForeignKey('RawMaterial', on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
    transaction_type = models.CharField(max_length=30, choices=StockTransactionType.choices)
    transaction_date = models.DateTimeField(default=timezone.now)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey('InventoryCategory', on_delete=models.PROTECT, related_name='transactions')
    location = models.CharField(max_length=100, null=True, blank=True)
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    reference = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    # Foreign keys to related entities
    purchase_order = models.ForeignKey('purchasing.PurchaseOrder', on_delete=models.SET_NULL, 
                                       null=True, blank=True, related_name='stock_transactions')
    sales_order = models.ForeignKey('sales.SalesOrder', on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='stock_transactions')
    work_order = models.ForeignKey('manufacturing.WorkOrder', on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='stock_transactions')
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='stock_transactions')
    
    class Meta:
        db_table = 'stock_transactions'
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['product', 'transaction_date']),
            models.Index(fields=['raw_material', 'transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['reference']),
            models.Index(fields=['category']),
            models.Index(fields=['batch_number']),
        ]
    
    def clean(self):
        # Ensure either product or raw_material is set, but not both
        if self.product and self.raw_material:
            raise ValidationError("A transaction cannot be associated with both a product and a raw material")
        if not self.product and not self.raw_material:
            raise ValidationError("A transaction must be associated with either a product or a raw material")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        item_code = self.product.product_code if self.product else self.raw_material.material_code
        item_type = "Product" if self.product else "Material"
        return f"{item_type} {item_code} - {self.get_transaction_type_display()} - {self.quantity}"


class StockMovement(BaseModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='movements', null=True, blank=True)
    raw_material = models.ForeignKey('RawMaterial', on_delete=models.CASCADE, related_name='movements', null=True, blank=True)
    from_category = models.ForeignKey('InventoryCategory', on_delete=models.PROTECT, related_name='outgoing_movements')
    to_category = models.ForeignKey('InventoryCategory', on_delete=models.PROTECT, related_name='incoming_movements')
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    movement_date = models.DateTimeField(default=timezone.now)
    reference_type = models.CharField(max_length=50, null=True, blank=True)
    reference_id = models.CharField(max_length=50, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='stock_movements')
    
    class Meta:
        db_table = 'stock_movements'
        ordering = ['-movement_date']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['raw_material']),
            models.Index(fields=['movement_date']),
        ]
    
    def clean(self):
        # Ensure either product or raw_material is set, but not both
        if self.product and self.raw_material:
            raise ValidationError("A movement cannot be associated with both a product and a raw material")
        if not self.product and not self.raw_material:
            raise ValidationError("A movement must be associated with either a product or a raw material")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        item_code = self.product.product_code if self.product else self.raw_material.material_code
        item_type = "Product" if self.product else "Material"
        return f"{item_type} {item_code} - {self.from_category.name} to {self.to_category.name}: {self.quantity}"




# New model for Tool
class ToolStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    IN_USE = 'IN_USE', 'In Use'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    BROKEN = 'BROKEN', 'Broken'
    RETIRED = 'RETIRED', 'Retired'


class Tool(BaseModel):
    tool_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    tool_type = models.CharField(max_length=50)
    size = models.CharField(max_length=50, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=ToolStatus.choices, default=ToolStatus.AVAILABLE)
    location = models.CharField(max_length=100, blank=True, null=True)
    
    # Tool specific attributes
    max_usage_count = models.IntegerField(null=True, blank=True)
    current_usage_count = models.IntegerField(default=0)
    last_maintenance_date = models.DateField(null=True, blank=True)
    maintenance_interval_days = models.IntegerField(default=90)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    # Physical characteristics
    dimensions = models.JSONField(null=True, blank=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    
    # Purchase information
    purchase_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier = models.ForeignKey('purchasing.Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_tools')
    
    class Meta:
        db_table = 'tools'
        ordering = ['tool_code']
        indexes = [
            models.Index(fields=['tool_type']),
            models.Index(fields=['status']),
            models.Index(fields=['next_maintenance_date']),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate next maintenance date if needed
        if self.last_maintenance_date and self.maintenance_interval_days:
            self.next_maintenance_date = self.last_maintenance_date + timezone.timedelta(days=self.maintenance_interval_days)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.tool_code} - {self.name} ({self.get_status_display()})"


# New model for tool usage tracking
class ToolUsage(BaseModel):
    tool = models.ForeignKey('Tool', on_delete=models.CASCADE, related_name='usages')
    work_order = models.ForeignKey('manufacturing.WorkOrder', on_delete=models.CASCADE, related_name='tool_usages')
    issued_date = models.DateTimeField(default=timezone.now)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='issued_tools')
    returned_date = models.DateTimeField(null=True, blank=True)
    returned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_tools')
    usage_count = models.IntegerField(default=1)
    condition_before = models.CharField(max_length=50, choices=[
        ('NEW', 'New'),
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor')
    ], default='GOOD')
    condition_after = models.CharField(max_length=50, choices=[
        ('GOOD', 'Good'),
        ('FAIR', 'Fair'),
        ('POOR', 'Poor'),
        ('BROKEN', 'Broken')
    ], null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'tool_usages'
        ordering = ['-issued_date']
        indexes = [
            models.Index(fields=['tool']),
            models.Index(fields=['work_order']),
            models.Index(fields=['issued_date']),
            models.Index(fields=['returned_date']),
        ]
    
    def save(self, *args, **kwargs):
        # Track tool usage and set tool status
        is_new = self.pk is None
        
        # Handle new tool usage
        if is_new:
            # Update tool status to IN_USE when issued
            if self.tool.status in [ToolStatus.AVAILABLE]:
                self.tool.status = ToolStatus.IN_USE
                self.tool.save(update_fields=['status'])
        
        # Handle tool return
        if not is_new and self.returned_date and not self._state.adding:
            # Get the original instance
            original = Tool.objects.get(pk=self.tool.pk)
            
            # Update tool usage count
            self.tool.current_usage_count += self.usage_count
            
            # Set tool status based on condition after return
            if self.condition_after == 'BROKEN':
                self.tool.status = ToolStatus.BROKEN
            else:
                # Check if tool needs maintenance based on usage count
                if (self.tool.max_usage_count and 
                    self.tool.current_usage_count >= self.tool.max_usage_count):
                    self.tool.status = ToolStatus.MAINTENANCE
                else:
                    self.tool.status = ToolStatus.AVAILABLE
            
            self.tool.save(update_fields=['status', 'current_usage_count'])
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.tool.tool_code} - {self.work_order.work_order_number}"