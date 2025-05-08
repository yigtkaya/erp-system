# inventory/models.py
from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseModel, Customer
from common.models import FileVersionManager, ContentType
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


class InventoryCategory(models.Model):
    CATEGORY_CHOICES = [
        ('HAMMADDE', 'Hammadde'),    # Raw Materials and Standard Parts
        ('PROSES', 'Proses'),        # Unfinished/Semi Products
        ('MAMUL', 'Mamül'),          # Finished and Single Products
        ('KARANTINA', 'Karantina'),  # Items needing decision
        ('HURDA', 'Hurda'),          # Scrap items
        ('TAKIMHANE', 'Takımhane')   # Tool storage
    ]
    
    name = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'inventory_categories'
        verbose_name = "Inventory Category"
        verbose_name_plural = "Inventory Categories"
    
    def __str__(self):
        return self.get_name_display()


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
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)
    inventory_category = models.ForeignKey(InventoryCategory, on_delete=models.PROTECT)
    material_type = models.CharField(max_length=20, choices=MaterialType.choices, null=True, blank=True)
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
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='technical_drawings')
    version = models.CharField(max_length=20)
    drawing_code = models.CharField(max_length=50)
    effective_date = models.DateField()
    is_current = models.BooleanField(default=True)
    revision_notes = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey('core.User', on_delete=models.PROTECT, null=True, blank=True)
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
    parent_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_items')
    child_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='used_in_products')
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