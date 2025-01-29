from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, ComponentType
from inventory.models.core import Product, RawMaterial
from .core import ManufacturingProcess

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
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
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
    semi_product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT, null=True, blank=True)
    process_config = models.ForeignKey(BOMProcessConfig, on_delete=models.PROTECT, null=True, blank=True)
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
            (self.process_config, ComponentType.MANUFACTURING_PROCESS)
        ]
        
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
