from django.db import models
from django.core.exceptions import ValidationError

class UnitOfMeasure(models.Model):
    id = models.AutoField(primary_key=True)
    unit_code = models.CharField(max_length=10, unique=True)
    unit_name = models.CharField(max_length=50)

    class Meta:
        verbose_name = "Unit of Measure"
        verbose_name_plural = "Units of Measure"

    def __str__(self):
        return f"{self.unit_code} ({self.unit_name})"

class RawMaterial(models.Model):
    material_code = models.CharField(max_length=50, unique=True)
    material_name = models.CharField(max_length=100)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Raw Material"
        verbose_name_plural = "Raw Materials"

    def __str__(self):
        return f"{self.material_code} - {self.material_name}"

class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('PURCHASE', 'Purchase'),
        ('CONSUMPTION', 'Consumption'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    id = models.AutoField(primary_key=True)
    product = models.ForeignKey('manufacturing.Product', on_delete=models.CASCADE, null=True, blank=True)
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, null=True, blank=True)
    quantity_change = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inventory Transaction"
        verbose_name_plural = "Inventory Transactions"
        indexes = [
            models.Index(fields=['transaction_date']),
        ]

    def clean(self):
        if not (self.product or self.material) or (self.product and self.material):
            raise ValidationError("Must specify either product or material, not both")

    def __str__(self):
        return f"{self.transaction_type} - {self.quantity_change}"
