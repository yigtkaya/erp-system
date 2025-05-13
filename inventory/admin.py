from django.contrib import admin
from .models import (
    Product, RawMaterial, InventoryCategory, UnitOfMeasure, ProductBOM,
    TechnicalDrawing, StockTransaction, StockMovement, Tool
)

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('material_code', 'material_name', 'material_type', 'current_stock', 'reserved_stock', 'available_stock', 'inventory_category')
    list_filter = ('material_type', 'inventory_category', 'is_active')
    search_fields = ('material_code', 'material_name', 'description')
    readonly_fields = ('available_stock',)
    fieldsets = (
        (None, {
            'fields': ('material_code', 'material_name', 'material_type', 'description', 'is_active')
        }),
        ('Stock Information', {
            'fields': ('current_stock', 'reserved_stock', 'available_stock', 'unit', 'inventory_category')
        }),
        ('Specifications', {
            'fields': ('width', 'height', 'thickness', 'diameter_mm', 'weight_per_unit')
        }),
        ('Inventory Management', {
            'fields': ('reorder_point', 'lead_time_days', 'tags')
        }),
    )
