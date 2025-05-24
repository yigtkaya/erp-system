# purchasing/admin.py
from django.contrib import admin
from .models import (
    Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseRequisition,
    PurchaseRequisitionItem, GoodsReceipt, GoodsReceiptItem,
    SupplierProductInfo
)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'contact_person', 'email', 'is_active')
    search_fields = ('code', 'name', 'email')
    list_filter = ('is_active', 'country')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'order_date', 'expected_delivery_date', 'status')
    search_fields = ('po_number', 'supplier__name')
    list_filter = ('status', 'order_date')
    date_hierarchy = 'order_date'

@admin.register(PurchaseRequisition)
class PurchaseRequisitionAdmin(admin.ModelAdmin):
    list_display = ('requisition_number', 'requested_by', 'request_date', 'status')
    search_fields = ('requisition_number', 'requested_by__username')
    list_filter = ('status', 'request_date')
    date_hierarchy = 'request_date'

@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'purchase_order', 'receipt_date', 'received_by')
    search_fields = ('receipt_number', 'purchase_order__po_number')
    date_hierarchy = 'receipt_date'

@admin.register(SupplierProductInfo)
class SupplierProductInfoAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'product', 'lead_time_days', 'minimum_quantity', 'is_active')
    list_filter = ('is_active', 'supplier')
    search_fields = ('supplier__name', 'product__product_code', 'supplier_product_code')