from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer
from inventory.models import Product
from model_utils import FieldTracker
import uuid
from datetime import datetime
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
    order_date = models.DateField(auto_now_add=True)
    order_receiving_date = models.DateField(null=True, blank=True, help_text="Date when the order was received from customer")
    deadline_date = models.DateField()
    kapsam_deadline_date = models.DateField(null=True, blank=True, help_text="Deadline date for kapsam")
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
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'order_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            raise ValidationError("Order number is required")
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.order_receiving_date and self.order_receiving_date > self.deadline_date:
            raise ValidationError("Order receiving date cannot be later than deadline date")
            
        if self.order_receiving_date and self.kapsam_deadline_date and self.order_receiving_date > self.kapsam_deadline_date:
            raise ValidationError("Order receiving date cannot be later than kapsam deadline date")

    def update_order_status(self):
        """Update order status based on items fulfillment"""
        all_items = self.items.all()
        if not all_items.exists():
            return
        
        # Check if all items are fully fulfilled
        all_fulfilled = True
        for item in all_items:
            if item.fulfilled_quantity < item.quantity:
                all_fulfilled = False
                break
        
        # Update status if needed
        if all_fulfilled and self.status != 'CLOSED':
            self.status = 'CLOSED'
            self.save(update_fields=['status'])
        elif not all_fulfilled and self.status == 'CLOSED':
            # If any item is not fulfilled but status is CLOSED, revert to OPEN
            self.status = 'OPEN'
            self.save(update_fields=['status'])

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

    def update_fulfilled_quantity(self):
        """Update fulfilled quantity based on associated shipments"""
        print(f"\nDEBUG: update_fulfilled_quantity called for Order Item {self.id}")
        print(f"DEBUG: Current state - Quantity: {self.quantity}, Fulfilled: {self.fulfilled_quantity}")
        
        # Get all shipments for this order item
        all_shipments = Shipping.objects.filter(order_item_id=self.id)
        print(f"DEBUG: Found shipments:")
        for ship in all_shipments:
            print(f"DEBUG: - Shipment {ship.shipping_no}: quantity={ship.quantity}")
        
        # Calculate total shipped quantity
        total_shipped = all_shipments.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        print(f"DEBUG: Total shipped quantity calculation: {total_shipped}")
        
        # Only update if the fulfilled quantity has changed
        if self.fulfilled_quantity != total_shipped:
            print(f"DEBUG: Updating fulfilled quantity from {self.fulfilled_quantity} to {total_shipped}")
            self.fulfilled_quantity = total_shipped
            # Set flag to indicate this update is from a shipment process
            self._update_from_shipment = True
            self.save(update_fields=['fulfilled_quantity'])
            # Clean up the flag after save
            delattr(self, '_update_from_shipment')
            
            # Update the order status
            print(f"DEBUG: Updating order status")
            self.sales_order.update_order_status()
        else:
            print(f"DEBUG: No change in fulfilled quantity, skipping update")

    def is_fully_fulfilled(self):
        """Check if the item is fully fulfilled"""
        return self.fulfilled_quantity >= self.quantity

    def __str__(self):
        return f"{self.sales_order.order_number} - {self.product.product_code}"

class Shipping(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipping_no = models.CharField(max_length=50, unique=True)
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
        unique_together = [['order', 'order_item', 'package_number']]

    def clean(self):
        super().clean()
        # Validate against order item quantity
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
        print(f"\nDEBUG: Shipping.save called for order item {self.order_item.id}")
        print(f"DEBUG: Current shipping quantity: {self.quantity}")
        
        if not self.shipping_no:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.shipping_no = f"SHP-{self.order.order_number}-{timestamp}"
            print(f"DEBUG: Generated shipping number: {self.shipping_no}")
            
        self.clean()
        print(f"DEBUG: Validation passed")
        
        # Check if this is a new shipment or an update
        is_new = self._state.adding
        print(f"DEBUG: Is new shipping record? {is_new}")
        
        super().save(*args, **kwargs)
        print(f"DEBUG: Shipping record saved successfully")

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
            if item.fulfilled_quantity < item.quantity:
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
