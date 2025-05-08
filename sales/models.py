# sales/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel, Customer, User
from inventory.models import Product
from common.models import FileVersionManager, ContentType


class OrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    IN_PRODUCTION = 'IN_PRODUCTION', 'In Production'
    READY = 'READY', 'Ready for Shipment'
    SHIPPED = 'SHIPPED', 'Shipped'
    DELIVERED = 'DELIVERED', 'Delivered'
    CANCELLED = 'CANCELLED', 'Cancelled'


class PaymentTerms(models.TextChoices):
    NET_30 = 'NET_30', 'Net 30 Days'
    NET_60 = 'NET_60', 'Net 60 Days'
    NET_90 = 'NET_90', 'Net 90 Days'
    ADVANCE = 'ADVANCE', 'Advance Payment'
    ON_DELIVERY = 'ON_DELIVERY', 'Payment on Delivery'
    INSTALLMENTS = 'INSTALLMENTS', 'Installments'


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'currencies'
        verbose_name_plural = 'Currencies'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class SalesOrder(BaseModel):
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_orders')
    order_date = models.DateField(default=timezone.now)
    delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('1.0'))
    payment_terms = models.CharField(max_length=20, choices=PaymentTerms.choices)
    customer_po_number = models.CharField(max_length=50, blank=True, null=True)
    salesperson = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sales_orders')
    shipping_address = models.TextField()
    billing_address = models.TextField()
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
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
    def net_amount(self):
        return self.total_amount - self.discount_amount + self.tax_amount
    
    @property
    def is_overdue(self):
        if self.status not in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            return timezone.now().date() > self.delivery_date
        return False
    
    def update_totals(self):
        """Recalculate order totals based on line items"""
        total = sum(item.extended_price for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"


class SalesOrderItem(BaseModel):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    delivery_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'sales_order_items'
        ordering = ['created_at']
    
    @property
    def extended_price(self):
        base_price = self.quantity * self.unit_price
        discount = base_price * (self.discount_percentage / 100)
        return base_price - discount
    
    @property
    def tax_amount(self):
        return self.extended_price * (self.tax_percentage / 100)
    
    @property
    def total_price(self):
        return self.extended_price + self.tax_amount
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")
        if self.unit_price < 0:
            raise ValidationError("Unit price cannot be negative")
    
    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.product_code}"


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
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('1.0'))
    payment_terms = models.CharField(max_length=20, choices=PaymentTerms.choices)
    salesperson = models.ForeignKey(User, on_delete=models.PROTECT, related_name='quotations')
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
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
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'sales_quotation_items'
        ordering = ['created_at']
    
    @property
    def extended_price(self):
        base_price = self.quantity * self.unit_price
        discount = base_price * (self.discount_percentage / 100)
        return base_price - discount
    
    def __str__(self):
        return f"{self.quotation.quotation_number} - {self.product.product_code}"


class CustomerPriceList(BaseModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='price_lists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    minimum_quantity = models.IntegerField(default=1)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'customer_price_lists'
        unique_together = ['customer', 'product', 'valid_from']
    
    def clean(self):
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError("Valid until date must be after valid from date")
    
    @property
    def is_valid(self):
        today = timezone.now().date()
        if not self.is_active:
            return False
        if today < self.valid_from:
            return False
        if self.valid_until and today > self.valid_until:
            return False
        return True
    
    def __str__(self):
        return f"{self.customer.code} - {self.product.product_code} - {self.unit_price}"