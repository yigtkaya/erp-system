from django.contrib import admin
from .models import Supplier, PurchaseOrder, PurchaseOrderItem

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'contact_email')
    search_fields = ('code', 'name')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'expected_delivery', 'status')
    list_filter = ('status', 'supplier')
    search_fields = ('order_number', 'supplier__name')

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity', 'unit_price', 'received_quantity')
    list_filter = ('purchase_order__status', 'product')
    search_fields = ('purchase_order__order_number', 'product__name')
    raw_id_fields = ('purchase_order', 'product')
