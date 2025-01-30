from django.contrib import admin
from .models import Product, RawMaterial, InventoryTransaction, InventoryCategory, UnitOfMeasure, TechnicalDrawing

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'product_name', 'current_stock', 'inventory_category', 'unit')
    list_filter = ('inventory_category', 'unit', 'product_type')
    search_fields = ('product_name', 'product_code', 'description')
    ordering = ('product_code',)

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('material_code', 'material_name', 'current_stock', 'inventory_category', 'unit')
    list_filter = ('inventory_category', 'unit')
    search_fields = ('material_name', 'material_code')
    ordering = ('material_code',)

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'quantity_change', 'transaction_date', 'performed_by')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('notes',)
    ordering = ('-transaction_date',)

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'unit_name')
    search_fields = ('unit_code', 'unit_name')
    ordering = ('unit_code',)

@admin.register(TechnicalDrawing)
class TechnicalDrawingAdmin(admin.ModelAdmin):
    list_display = ('drawing_code', 'product', 'version', 'is_current', 'effective_date')
    list_filter = ('is_current', 'effective_date')
    search_fields = ('drawing_code', 'version', 'product__product_name')
    ordering = ('-effective_date',)
