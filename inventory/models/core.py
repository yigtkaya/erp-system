from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer, ProductType
from django.core.validators import MinValueValidator

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
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def clean(self):
        if self.product_type == ProductType.SINGLE and self.customer:
            raise ValidationError("Single parts shouldn't be customer-specific")

    def __str__(self):
        return f"{self.product_code} - {self.product_name}"

class TechnicalDrawing(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    version = models.CharField(max_length=20)
    drawing_code = models.CharField(max_length=50)
    drawing_url = models.URLField(max_length=500)
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

    def __str__(self):
        return f"{self.drawing_code} v{self.version}"

class RawMaterial(BaseModel):
    material_code = models.CharField(max_length=50, unique=True)
    material_name = models.CharField(max_length=100)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Raw Material"
        verbose_name_plural = "Raw Materials"

    def __str__(self):
        return f"{self.material_code} - {self.material_name}"
