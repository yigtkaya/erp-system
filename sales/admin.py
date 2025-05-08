# sales/admin.py
from django.contrib import admin
from .models import (
    Currency, SalesOrder, SalesOrderItem, SalesQuotation,
    SalesQuotationItem, CustomerPriceList
)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'is_active')
    search_fields = ('code', 'name')

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'order_date', 'delivery_date', 'status', 'total_amount')
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

@admin.register(CustomerPriceList)
class CustomerPriceListAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'unit_price', 'currency', 'valid_from', 'is_active')
    list_filter = ('is_active', 'currency')
    search_fields = ('customer__name', 'product__product_code')