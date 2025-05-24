# sales/admin.py
from django.contrib import admin
from .models import SalesOrder, SalesOrderItem, SalesQuotation, SalesQuotationItem

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'order_date', 'delivery_date', 'status')
    search_fields = ('order_number', 'customer__name')
    list_filter = ('status', 'order_date')
    date_hierarchy = 'order_date'

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1

@admin.register(SalesQuotation)
class SalesQuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'customer', 'quotation_date', 'valid_until', 'status')
    search_fields = ('quotation_number', 'customer__name')
    list_filter = ('status', 'quotation_date')
    date_hierarchy = 'quotation_date'