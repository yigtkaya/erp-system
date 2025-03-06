from django.db import models
from django.core.exceptions import ValidationError
from erp_core.models import BaseModel, User, Customer
from inventory.models import Product
from model_utils import FieldTracker
import uuid
from datetime import datetime
from django.db.models import Sum, F
from django.utils import timezone

class SalesOrder(BaseModel):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed')
    ]
    
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    order_date = models.DateField(auto_now_add=True)
    order_receiving_date = models.DateField(null=True, blank=True, help_text="Date when the order was received from customer")
    deadline_date = models.DateField()
    kapsam_deadline_date = models.DateField(null=True, blank=True, help_text="Deadline date for kapsam")
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
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'order_date']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Get the last order number for the current year and month
            year = timezone.now().year
            month = timezone.now().month
            last_order = SalesOrder.objects.filter(
                created_at__year=year,
                created_at__month=month
            ).order_by('-order_number').first()

            # Extract the sequence number from the last order number or start from 0
            if last_order and last_order.order_number:
                try:
                    last_sequence = int(last_order.order_number[-4:])
                except ValueError:
                    last_sequence = 0
            else:
                last_sequence = 0

            # Generate new order number: SO-YYYYMM-XXXX
            self.order_number = f'SO-{year}{month:02d}-{(last_sequence + 1):04d}'

        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.status in ['PENDING_APPROVAL', 'APPROVED'] and not self.order_receiving_date:
            raise ValidationError("Order receiving date is required for orders pending approval or approved")
            
        if self.status in ['PENDING_APPROVAL', 'APPROVED'] and not self.kapsam_deadline_date:
            raise ValidationError("Kapsam deadline date is required for orders pending approval or approved")

        if self.order_receiving_date and self.order_receiving_date > self.deadline_date:
            raise ValidationError("Order receiving date cannot be later than deadline date")
            
        if self.kapsam_deadline_date and self.kapsam_deadline_date > self.deadline_date:
            raise ValidationError("Kapsam deadline date cannot be later than main deadline date")
            
        if self.order_receiving_date and self.kapsam_deadline_date and self.order_receiving_date > self.kapsam_deadline_date:
            raise ValidationError("Order receiving date cannot be later than kapsam deadline date")

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipping_no = models.CharField(max_length=50, unique=True)
    shipping_date = models.DateField()
    shipping_amount = models.IntegerField()  # Changed to IntegerField since it's smallint in the table
    order = models.ForeignKey(SalesOrder, on_delete=models.PROTECT, related_name='shipments')
    shipping_note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.shipping_no} - {self.order.order_number}"

    class Meta:
        ordering = ['-shipping_date']
        verbose_name = 'Shipping'
        verbose_name_plural = 'Shippings'

    def save(self, *args, **kwargs):
        if not self.shipping_no:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.shipping_no = f"SHP-{self.order.order_number}-{timestamp}"
        super().save(*args, **kwargs)

class ShipmentItem(BaseModel):
    shipment = models.ForeignKey(Shipping, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(SalesOrderItem, on_delete=models.PROTECT, related_name='shipment_items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    package_number = models.PositiveIntegerField(default=1)
    lot_number = models.CharField(max_length=50, blank=True, null=True)
    serial_numbers = models.JSONField(default=list, blank=True, help_text="List of serial numbers for tracked items")
    
    class Meta:
        ordering = ['package_number', 'id']
        unique_together = [['shipment', 'order_item', 'package_number']]

    def clean(self):
        super().clean()
        # Validate against order item quantity
        total_shipped = (
            ShipmentItem.objects
            .filter(order_item=self.order_item)
            .exclude(pk=self.pk)
            .aggregate(total=Sum('quantity'))['total'] or 0
        ) + self.quantity
        
        if total_shipped > self.order_item.quantity:
            raise ValidationError({
                'quantity': f'Total shipped quantity ({total_shipped}) exceeds ordered quantity ({self.order_item.quantity})'
            })

    def save(self, *args, **kwargs):
        if not self.product_id:
            self.product = self.order_item.product
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.shipment.shipping_no} - {self.product.product_code} ({self.quantity})"
