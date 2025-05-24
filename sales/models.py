# sales/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel, Customer
from inventory.models import Product


class OrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    IN_PRODUCTION = 'IN_PRODUCTION', 'In Production'
    READY = 'READY', 'Ready for Shipment'
    SHIPPED = 'SHIPPED', 'Shipped'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'


class SalesOrder(BaseModel):
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_orders')
    order_date = models.DateField(default=timezone.now)
    delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    customer_po_number = models.CharField(max_length=50, blank=True, null=True)
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sales_orders')
    shipping_address = models.TextField()
    billing_address = models.TextField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'sales_orders'
        ordering = ['-order_date', '-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer', 'order_date']),
            models.Index(fields=['status']),
        ]
    
    def clean(self):
        if self.delivery_date < self.order_date:
            raise ValidationError("Delivery date cannot be before order date")
    
    @property
    def is_overdue(self):
        if self.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            return timezone.now().date() > self.delivery_date
        return False
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"


class SalesOrderItem(BaseModel):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    delivery_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'sales_order_items'
        ordering = ['created_at']
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")
    
    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.product_code} (Qty: {self.quantity})"


class SalesQuotation(BaseModel):
    quotation_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='quotations')
    quotation_date = models.DateField(default=timezone.now)
    valid_until = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ], default='DRAFT')
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='quotations')
    notes = models.TextField(blank=True, null=True)
    converted_to_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'sales_quotations'
        ordering = ['-quotation_date']
    
    def clean(self):
        if self.valid_until < self.quotation_date:
            raise ValidationError("Valid until date must be after quotation date")
    
    @property
    def is_expired(self):
        return timezone.now().date() > self.valid_until and self.status not in ['ACCEPTED', 'REJECTED']
    
    def __str__(self):
        return f"{self.quotation_number} - {self.customer.name}"


class SalesQuotationItem(BaseModel):
    quotation = models.ForeignKey(SalesQuotation, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'sales_quotation_items'
        ordering = ['created_at']
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")
    
    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.product.product_code} (Qty: {self.quantity})"