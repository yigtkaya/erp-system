from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer
from inventory.models import Product
from model_utils import FieldTracker
import uuid
from django.db.models import Sum, F
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import connection

class SalesOrder(BaseModel):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    created_at = models.DateField(auto_now_add=True)
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='approved_sales_orders')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN'
    )
    tracker = FieldTracker(fields=['status'])
    
    def __str__(self):
        return f"{self.order_number} - {self.customer.name}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            raise ValidationError("Order number is required")
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()

    def update_order_status(self):
        """Update order status based on items fulfillment"""
        all_items = self.items.all()
        if not all_items.exists():
            return
        
        # Check if all items are fully fulfilled
        all_fulfilled = True
        for item in all_items:
            if item.fulfilled_quantity < item.ordered_quantity:
                all_fulfilled = False
                break
        
        # Update status if needed
        if all_fulfilled and self.status != 'CLOSED':
            self.status = 'CLOSED'
            self.save(update_fields=['status'])
        elif not all_fulfilled and self.status == 'CLOSED':
            self.status = 'OPEN'
            self.save(update_fields=['status'])

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    ordered_quantity = models.IntegerField()
    fulfilled_quantity = models.IntegerField(default=0)
    receiving_date = models.DateField(null=True, blank=True, help_text="Date when the order item was received from customer")
    deadline_date = models.DateField(null=True, blank=True, help_text="Deadline date for the order item")
    kapsam_deadline_date = models.DateField(null=True, blank=True, help_text="Deadline date for kapsam for the order item")

    def clean(self):
        if self.fulfilled_quantity > self.ordered_quantity:
            raise ValidationError("Fulfilled quantity cannot exceed ordered quantity")
        
        if self.receiving_date and self.deadline_date and self.receiving_date > self.deadline_date:
            raise ValidationError("Receiving date cannot be later than deadline date")

        if self.receiving_date and self.kapsam_deadline_date and self.receiving_date > self.kapsam_deadline_date:
            raise ValidationError("Receiving date cannot be later than kapsam deadline date")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def update_fulfilled_quantity(self):
        """Update fulfilled quantity based on associated shipments"""
        all_shipments = Shipping.objects.filter(order_item_id=self.id)
        total_shipped = all_shipments.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        if self.fulfilled_quantity != total_shipped:
            self.fulfilled_quantity = total_shipped
            # Indicate update is coming from the shipping process
            self._update_from_shipment = True
            self.save(update_fields=['fulfilled_quantity'])
            delattr(self, '_update_from_shipment')
            self.sales_order.update_order_status()

    def is_fully_fulfilled(self):
        """Check if the item is fully fulfilled"""
        return self.fulfilled_quantity >= self.ordered_quantity

    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.product_code}"

class Shipping(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipping_no = models.CharField(max_length=50)
    shipping_date = models.DateField()
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='shipments')
    order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, related_name='shipments')
    quantity = models.PositiveIntegerField()
    package_number = models.PositiveIntegerField(default=1)
    shipping_note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.shipping_no} - {self.order.order_number}"

    class Meta:
        ordering = ['-shipping_date']
        verbose_name = 'Shipping'
        verbose_name_plural = 'Shippings'
        unique_together = [['shipping_no', 'order', 'order_item']]

    def clean(self):
        super().clean()
        total_shipped = (
            Shipping.objects
            .filter(order_item=self.order_item)
            .exclude(pk=self.pk)
            .aggregate(total=Sum('quantity'))['total'] or 0
        ) + self.quantity
        
        if total_shipped > self.order_item.ordered_quantity:
            raise ValidationError({
                'quantity': f'Total shipped quantity ({total_shipped}) exceeds ordered quantity ({self.order_item.ordered_quantity})'
            })

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self._state.adding
        super().save(*args, **kwargs)

@receiver(post_delete, sender=Shipping)
def update_on_shipment_delete(sender, instance, **kwargs):
    """Update fulfilled quantity and order status when a shipment is deleted"""
    if instance.order_item:
        # Get the current total shipped quantity
        total_shipped = Shipping.objects.filter(
            order_item=instance.order_item
        ).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        # Update the order item's fulfilled quantity directly
        SalesOrderItem.objects.filter(id=instance.order_item.id).update(
            fulfilled_quantity=total_shipped
        )
        
        # Refresh the order item from the database
        instance.order_item.refresh_from_db()
        
        # Check if all items in the order are fully fulfilled
        all_items_fulfilled = True
        for item in instance.order.items.all():
            item.refresh_from_db()  # Ensure we have the latest data
            if item.fulfilled_quantity < item.ordered_quantity:
                all_items_fulfilled = False
                break
        
        # Update order status if needed
        if all_items_fulfilled and instance.order.status != 'CLOSED':
            instance.order.status = 'CLOSED'
            instance.order.save(update_fields=['status'])
        elif not all_items_fulfilled and instance.order.status == 'CLOSED':
            instance.order.status = 'OPEN'
            instance.order.save(update_fields=['status'])

@receiver(post_save, sender=SalesOrderItem)
def check_order_status_on_item_change(sender, instance, **kwargs):
    """Check and update order status when an order item changes"""
    # Skip if this update is from a shipment process
    # as the update_fulfilled_quantity method already updates the order status
    if hasattr(instance, '_update_from_shipment') and instance._update_from_shipment:
        return
        
    if instance.sales_order:
        instance.sales_order.update_order_status()
