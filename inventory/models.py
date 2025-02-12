from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer, ProductType, MaterialType
from django.core.validators import MinValueValidator
import pathlib 

class InventoryCategory(models.Model):
    CATEGORY_CHOICES = [
        ('HAMMADDE', 'Hammadde'),  # Raw Materials and Standard Parts
        ('PROSES', 'Proses'),      # Unfinished/Semi Products
        ('MAMUL', 'Mamül'),        # Finished and Semi-finished Products
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
    product_type = models.CharField(max_length=20, choices=ProductType.choices)
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

class TechnicalDrawing(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    version = models.CharField(max_length=20)
    drawing_code = models.CharField(max_length=50)
    drawing_file = models.FileField(upload_to='technical_drawings/%Y/%m/%d/', max_length=500, blank=True, null=True)
    effective_date = models.DateField()
    is_current = models.BooleanField(default=True)
    revision_notes = models.CharField(max_length=500, blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_drawings')

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
