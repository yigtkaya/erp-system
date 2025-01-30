from django.contrib import admin
from .models import SalesOrder, SalesOrderItem

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'order_date', 'deadline_date', 'approved_by')
    list_filter = ('order_date', 'deadline_date')
    search_fields = ('order_number', 'customer__name', 'notes')
    ordering = ('-created_at',)
    date_hierarchy = 'order_date'

@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ('sales_order', 'product', 'quantity', 'fulfilled_quantity')
    list_filter = ('product',)
    search_fields = ('sales_order__order_number', 'product__product_name')
    ordering = ('sales_order', 'product')
