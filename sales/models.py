from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer
from inventory.models import Product
from model_utils import FieldTracker
import uuid
from datetime import datetime

class SalesOrder(BaseModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed')
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    order_date = models.DateField(auto_now_add=True)
    deadline_date = models.DateField()
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_sales_orders')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    tracker = FieldTracker(fields=['status'])
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"

    class Meta:
        ordering = ['-order_date']

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    fulfilled_quantity = models.IntegerField(default=0)

    def clean(self):
        if self.fulfilled_quantity > self.quantity:
            raise ValidationError("Fulfilled quantity cannot exceed ordered quantity")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.product_code}"

class Shipping(BaseModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PICKED_UP', 'Picked Up'),
        ('IN_TRANSIT', 'In Transit'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('FAILED', 'Failed Delivery'),
        ('RETURNED', 'Returned')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipping_no = models.CharField(max_length=50, unique=True)
    shipping_date = models.DateField()
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name='shipments')
    shipping_note = models.TextField(blank=True, null=True)
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    # Carrier Information
    carrier = models.CharField(max_length=100, blank=True, null=True)
    carrier_service = models.CharField(max_length=100, blank=True, null=True)
    
    # Package Details
    package_weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Weight in kg")
    package_length = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Length in cm")
    package_width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Width in cm")
    package_height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Height in cm")
    
    # Shipping Address
    shipping_address_line1 = models.CharField(max_length=255, null=True, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True, null=True)
    shipping_city = models.CharField(max_length=100, null=True, blank=True)
    shipping_state = models.CharField(max_length=100, null=True, blank=True)
    shipping_country = models.CharField(max_length=100, null=True, blank=True)
    shipping_postal_code = models.CharField(max_length=20, null=True, blank=True)
    
    # Insurance
    is_insured = models.BooleanField(default=False)
    insurance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.shipping_no} - {self.order.order_number}"

    class Meta:
        ordering = ['-shipping_date']
        verbose_name = 'Shipping'
        verbose_name_plural = 'Shippings'

    def clean(self):
        if self.shipping_date < self.order.order_date:
            raise ValidationError("Shipping date cannot be earlier than order date")
        if self.actual_delivery_date and self.shipping_date > self.actual_delivery_date:
            raise ValidationError("Shipping date cannot be later than delivery date")
        if self.estimated_delivery_date and self.shipping_date > self.estimated_delivery_date:
            raise ValidationError("Shipping date cannot be later than estimated delivery date")

    def save(self, *args, **kwargs):
        if not self.shipping_no:
            # Generate shipping number based on order number and timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.shipping_no = f"SHP-{self.order.order_number}-{timestamp}"
        self.clean()
        super().save(*args, **kwargs)
        
    @property
    def delivery_status(self):
        if self.status == 'DELIVERED' and self.actual_delivery_date:
            if self.actual_delivery_date <= self.estimated_delivery_date:
                return 'On Time'
            return 'Delayed'
        return self.get_status_display()
    
    @property
    def transit_time(self):
        if self.actual_delivery_date and self.shipping_date:
            return (self.actual_delivery_date - self.shipping_date).days
        return None
