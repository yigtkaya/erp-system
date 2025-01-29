from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import User
from .core import Product, RawMaterial

class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJUST', 'Adjustment'),
        ('RETURN', 'Return'),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT, null=True, blank=True)
    material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT, null=True, blank=True)
    quantity_change = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    transaction_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='transactions_performed')
    verified_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='transactions_verified')
    notes = models.TextField(blank=True, null=True)

    def clean(self):
        if not bool(self.product) != bool(self.material):
            raise ValidationError("Either product or material must be set, but not both.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
        # Update stock levels
        if self.product:
            self.product.current_stock += self.quantity_change
            self.product.save()
        elif self.material:
            self.material.current_stock += self.quantity_change
            self.material.save()

    def __str__(self):
        item = self.product or self.material
        return f"{self.transaction_type} - {item} - {self.quantity_change}"
