from django.contrib import admin
from .models import SalesOrder, SalesOrderItem, Shipping

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1
    readonly_fields = ['fulfilled_quantity', 'ordered_quantity']

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'created_at', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'customer__name']
    readonly_fields = ['order_number']
    inlines = [SalesOrderItemInline]
    date_hierarchy = 'created_at'

@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ['shipping_no', 'order', 'shipping_date', 'quantity', 'package_number']
    list_filter = ['shipping_date']
    search_fields = ['shipping_no', 'order__order_number']
