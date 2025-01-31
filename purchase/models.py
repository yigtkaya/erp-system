from django.db import models
from erp_core.models import BaseModel, ProductType
from inventory.models import Product
from model_utils import FieldTracker

class Supplier(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    contact_email = models.EmailField()
    payment_terms = models.TextField()

class PurchaseOrder(BaseModel):
    ORDER_STATUS = [
        ('DRAFT', 'Draft'),
        ('PO_ISSUED', 'PO Issued'),
        ('PART_RECEIVED', 'Partially Received'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    expected_delivery = models.DateField()
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='DRAFT')

class PurchaseOrderItem(BaseModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, limit_choices_to={'product_type': ProductType.STANDARD_PART})
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.IntegerField(default=0)
    tracker = FieldTracker(fields=['received_quantity'])

    class Meta:
        ordering = ['created_at']
