# purchasing/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel
from inventory.models import Product
from common.models import FileVersionManager, ContentType


class Supplier(BaseModel):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'suppliers'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class PurchaseOrderStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    REQUESTED = 'REQUESTED', 'Requested'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    SENT = 'SENT', 'Sent to Supplier'
    PARTIAL = 'PARTIAL', 'Partially Received'
    RECEIVED = 'RECEIVED', 'Fully Received'
    CANCELLED = 'CANCELLED', 'Cancelled'


class PurchaseOrder(BaseModel):
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    order_date = models.DateField(default=timezone.now)
    expected_delivery_date = models.DateField()
    status = models.CharField(max_length=20, choices=PurchaseOrderStatus.choices, default=PurchaseOrderStatus.DRAFT)
    currency = models.ForeignKey('sales.Currency', on_delete=models.PROTECT)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=6, default=Decimal('1.0'))
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='purchase_orders')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    approval_date = models.DateTimeField(null=True, blank=True)
    supplier_reference = models.CharField(max_length=100, blank=True, null=True)
    shipping_address = models.TextField()
    billing_address = models.TextField()
    payment_terms = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-order_date', '-created_at']
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['supplier', 'order_date']),
            models.Index(fields=['status']),
        ]
    
    @property
    def net_amount(self):
        return self.total_amount + self.tax_amount
    
    def update_totals(self):
        """Recalculate order totals based on line items"""
        items = self.items.all()
        total = sum(item.extended_price for item in items)
        tax = sum(item.tax_amount for item in items)
        self.total_amount = total
        self.tax_amount = tax
        self.save(update_fields=['total_amount', 'tax_amount'])
    
    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"


class PurchaseOrderItem(BaseModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    expected_delivery_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'purchase_order_items'
        ordering = ['created_at']
    
    @property
    def extended_price(self):
        return self.quantity_ordered * self.unit_price
    
    @property
    def tax_amount(self):
        return self.extended_price * (self.tax_percentage / 100)
    
    @property
    def total_price(self):
        return self.extended_price + self.tax_amount
    
    @property
    def is_fully_received(self):
        return self.quantity_received >= self.quantity_ordered
    
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product.product_code}"


class PurchaseRequisition(BaseModel):
    requisition_number = models.CharField(max_length=50, unique=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='purchase_requisitions')
    request_date = models.DateField(default=timezone.now)
    required_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CONVERTED', 'Converted to PO'),
        ('CANCELLED', 'Cancelled'),
    ], default='DRAFT')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requisitions')
    approval_date = models.DateTimeField(null=True, blank=True)
    department = models.ForeignKey('core.Department', on_delete=models.PROTECT)
    notes = models.TextField(blank=True, null=True)
    converted_to_po = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'purchase_requisitions'
        ordering = ['-request_date']
    
    def __str__(self):
        return f"{self.requisition_number} - {self.requested_by.username}"


class PurchaseRequisitionItem(BaseModel):
    requisition = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    estimated_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    preferred_supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'purchase_requisition_items'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.requisition.requisition_number} - {self.product.product_code}"


class GoodsReceipt(BaseModel):
    receipt_number = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='receipts')
    receipt_date = models.DateTimeField(default=timezone.now)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='goods_receipts')
    supplier_delivery_note = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'goods_receipts'
        ordering = ['-receipt_date']
    
    def __str__(self):
        return f"{self.receipt_number} - {self.purchase_order.po_number}"
    
    # File management methods
    def upload_delivery_note(self, file, notes=None, user=None):
        """Upload delivery note document"""
        return FileVersionManager.create_version(
            file=file,
            content_type=ContentType.PURCHASE_ORDER,
            object_id=str(self.id),
            notes=notes,
            user=user
        )


class GoodsReceiptItem(BaseModel):
    receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='items')
    po_item = models.ForeignKey(PurchaseOrderItem, on_delete=models.PROTECT)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_accepted = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_rejected = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    rejection_reason = models.TextField(blank=True, null=True)
    storage_location = models.CharField(max_length=100, blank=True, null=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        db_table = 'goods_receipt_items'
        ordering = ['created_at']
    
    def clean(self):
        if self.quantity_accepted + self.quantity_rejected != self.quantity_received:
            raise ValidationError("Accepted + Rejected quantity must equal Received quantity")
    
    def __str__(self):
        return f"{self.receipt.receipt_number} - {self.po_item.product.product_code}"


class SupplierPriceList(BaseModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='price_lists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.ForeignKey('sales.Currency', on_delete=models.PROTECT)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    minimum_quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    lead_time_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'supplier_price_lists'
        unique_together = ['supplier', 'product', 'valid_from']
    
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
        return f"{self.supplier.code} - {self.product.product_code} - {self.unit_price}"