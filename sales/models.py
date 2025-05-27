# sales/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
import uuid
from core.models import BaseModel, Customer
from inventory.models import Product


class OrderItemStatus(models.TextChoices):
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
    customer_po_number = models.CharField(max_length=50, blank=True, null=True)
    salesperson = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sales_orders')
    shipping_address = models.TextField()
    billing_address = models.TextField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'sales_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['customer']),
        ]
    
    @property
    def status(self):
        """Derive overall order status from item statuses"""
        if not self.items.exists():
            return OrderItemStatus.DRAFT
        
        item_statuses = set(self.items.values_list('status', flat=True))
        
        # If any item is cancelled, check if all are cancelled
        if OrderItemStatus.CANCELLED in item_statuses:
            if len(item_statuses) == 1:  # All items are cancelled
                return OrderItemStatus.CANCELLED
        
        # If any item is delivered, check if all are delivered
        if OrderItemStatus.DELIVERED in item_statuses:
            if len(item_statuses) == 1:  # All items are delivered
                return OrderItemStatus.DELIVERED
        
        # Priority order for mixed statuses
        status_priority = [
            OrderItemStatus.SHIPPED,
            OrderItemStatus.READY,
            OrderItemStatus.IN_PRODUCTION,
            OrderItemStatus.CONFIRMED,
            OrderItemStatus.DRAFT,
        ]
        
        for status in status_priority:
            if status in item_statuses:
                return status
        
        return OrderItemStatus.DRAFT
    
    @property
    def status_summary(self):
        """Get a summary of item statuses"""
        if not self.items.exists():
            return {}
        
        from django.db.models import Count
        return dict(
            self.items.values('status')
            .annotate(count=Count('status'))
            .values_list('status', 'count')
        )
    
    @property
    def earliest_delivery_date(self):
        """Returns the earliest delivery date from all order items"""
        delivery_dates = self.items.values_list('delivery_date', flat=True)
        return min(delivery_dates) if delivery_dates else None
    
    @property
    def earliest_kapsam_deadline(self):
        """Returns the earliest kapsam deadline date from all order items"""
        kapsam_dates = self.items.exclude(kapsam_deadline_date__isnull=True).values_list('kapsam_deadline_date', flat=True)
        return min(kapsam_dates) if kapsam_dates else None
    
    @property
    def latest_kapsam_deadline(self):
        """Returns the latest kapsam deadline date from all order items"""
        kapsam_dates = self.items.exclude(kapsam_deadline_date__isnull=True).values_list('kapsam_deadline_date', flat=True)
        return max(kapsam_dates) if kapsam_dates else None
    
    @property
    def is_overdue(self):
        """Check if any order item is overdue"""
        active_statuses = [OrderItemStatus.CONFIRMED, OrderItemStatus.IN_PRODUCTION, OrderItemStatus.READY, OrderItemStatus.SHIPPED]
        return any(
            item.is_overdue for item in self.items.filter(status__in=active_statuses)
        )
    
    @property
    def is_kapsam_overdue(self):
        """Check if any order item has overdue kapsam deadline"""
        active_statuses = [OrderItemStatus.CONFIRMED, OrderItemStatus.IN_PRODUCTION, OrderItemStatus.READY, OrderItemStatus.SHIPPED]
        return any(
            item.is_kapsam_overdue for item in self.items.filter(status__in=active_statuses)
        )
    
    @property
    def kapsam_status(self):
        """Get overall kapsam status for the order"""
        completed_statuses = [OrderItemStatus.DELIVERED, OrderItemStatus.CANCELLED]
        active_items = self.items.exclude(status__in=completed_statuses, kapsam_deadline_date__isnull=True)
        
        if not active_items.exists():
            return 'COMPLETED'
        
        items_with_kapsam = active_items.exclude(kapsam_deadline_date__isnull=True)
        if not items_with_kapsam.exists():
            return 'NO_DEADLINE'
        
        today = timezone.now().date()
        
        # Check if any item is overdue
        if any(item.kapsam_deadline_date < today for item in items_with_kapsam):
            return 'OVERDUE'
        
        # Check if any item is due within 3 days
        if any(item.kapsam_deadline_date <= today + timedelta(days=3) for item in items_with_kapsam):
            return 'DUE_SOON'
        
        # Check if any item is due within a week
        if any(item.kapsam_deadline_date <= today + timedelta(days=7) for item in items_with_kapsam):
            return 'DUE_THIS_WEEK'
        
        return 'ON_TRACK'
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"


class SalesOrderItem(BaseModel):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=OrderItemStatus.choices, default=OrderItemStatus.DRAFT)
    order_date = models.DateField(default=timezone.now)
    delivery_date = models.DateField()
    kapsam_deadline_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'sales_order_items'
        ordering = ['order_date', 'created_at']
        indexes = [
            models.Index(fields=['order_date']),
            models.Index(fields=['delivery_date']),
            models.Index(fields=['kapsam_deadline_date']),
            models.Index(fields=['status']),
        ]
    
    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("Quantity must be positive")
        if self.delivery_date < self.order_date:
            raise ValidationError("Delivery date cannot be before order date")
        if self.kapsam_deadline_date and self.kapsam_deadline_date < self.order_date:
            raise ValidationError("Kapsam deadline date cannot be before order date")
    
    @property
    def is_overdue(self):
        """Check if this item is overdue based on delivery date"""
        if self.status in [OrderItemStatus.DELIVERED, OrderItemStatus.CANCELLED]:
            return False
        return timezone.now().date() > self.delivery_date
    
    @property
    def is_kapsam_overdue(self):
        """Check if this item is overdue based on kapsam deadline date"""
        if self.status in [OrderItemStatus.DELIVERED, OrderItemStatus.CANCELLED]:
            return False
        if not self.kapsam_deadline_date:
            return False
        return timezone.now().date() > self.kapsam_deadline_date
    
    @property
    def shipped_quantity(self):
        """Get total shipped quantity for this order item"""
        return self.shipments.aggregate(total=Sum('quantity'))['total'] or 0
    
    @property
    def remaining_quantity(self):
        """Get remaining quantity to be shipped"""
        return self.quantity - self.shipped_quantity
    
    @property
    def is_fully_shipped(self):
        """Check if this order item is fully shipped"""
        return self.shipped_quantity >= self.quantity
    
    @property
    def is_partially_shipped(self):
        """Check if this order item is partially shipped"""
        shipped = self.shipped_quantity
        return 0 < shipped < self.quantity
    
    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.product_code} (Qty: {self.quantity}) - {self.get_status_display()}"


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


class Shipping(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipping_no = models.CharField(max_length=50)
    shipping_date = models.DateField()
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='shipments')
    order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, related_name='shipments')
    quantity = models.PositiveIntegerField()
    package_number = models.PositiveIntegerField(default=1)
    shipping_note = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sales_shipments'
        ordering = ['-shipping_date']
        verbose_name = 'Shipping'
        verbose_name_plural = 'Shippings'
        unique_together = [['shipping_no', 'order', 'order_item']]
        indexes = [
            models.Index(fields=['shipping_no']),
            models.Index(fields=['shipping_date']),
            models.Index(fields=['order']),
            models.Index(fields=['order_item']),
        ]

    def clean(self):
        super().clean()
        if self.quantity <= 0:
            raise ValidationError({'quantity': 'Quantity must be positive'})
        
        # Calculate total shipped quantity for this order item
        total_shipped = (
            Shipping.objects
            .filter(order_item=self.order_item)
            .exclude(pk=self.pk)
            .aggregate(total=Sum('quantity'))['total'] or 0
        ) + self.quantity
        
        if total_shipped > self.order_item.quantity:
            raise ValidationError({
                'quantity': f'Total shipped quantity ({total_shipped}) exceeds ordered quantity ({self.order_item.quantity})'
            })

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self._state.adding
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shipping_no} - {self.order.order_number}"