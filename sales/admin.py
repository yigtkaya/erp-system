from django.contrib import admin
from .models import SalesOrder, SalesOrderItem, Shipping, ShipmentItem

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1
    readonly_fields = ['fulfilled_quantity']

class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 1
    readonly_fields = ['product']

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'order_date', 'deadline_date', 'status']
    list_filter = ['status', 'order_date']
    search_fields = ['order_number', 'customer__name']
    readonly_fields = ['order_number']
    inlines = [SalesOrderItemInline]
    date_hierarchy = 'order_date'

@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ['shipping_no', 'order', 'shipping_date', 'shipping_amount']
    search_fields = ['shipping_no', 'order__order_number']
    readonly_fields = ['shipping_no']
    date_hierarchy = 'shipping_date'
    fieldsets = (
        ('Basic Information', {
            'fields': ('shipping_no', 'order', 'shipping_date', 'shipping_amount', 'shipping_note')
        }),
    )

@admin.register(ShipmentItem)
class ShipmentItemAdmin(admin.ModelAdmin):
    list_display = ['shipment', 'order_item', 'product', 'quantity', 'package_number']
    list_filter = ['package_number']
    search_fields = ['shipment__shipping_no', 'product__product_code']
    readonly_fields = ['product']
