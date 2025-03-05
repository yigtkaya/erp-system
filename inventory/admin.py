from django.contrib import admin
from .models import Product, RawMaterial, InventoryTransaction, InventoryCategory, UnitOfMeasure, TechnicalDrawing, Tool, Holder

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'product_code', 
        'product_name', 
        'current_stock', 
        'inventory_category'
    ]
    list_filter = [
        'inventory_category'
    ]
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

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('stock_code', 'product_code', 'tool_type', 'status', 'quantity', 'row', 'column')
    list_filter = ('tool_type', 'status', 'tool_material')
    search_fields = ('stock_code', 'product_code', 'description')
    ordering = ('stock_code',)
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('stock_code', 'product_code', 'supplier_name', 'tool_type', 'status', 'description')
        }),
        ('Pricing', {
            'fields': ('unit_price_tl', 'unit_price_euro', 'unit_price_usd')
        }),
        ('Tool Specifications', {
            'fields': ('tool_insert_code', 'tool_material', 'tool_diameter', 'tool_length', 'tool_width',
                      'tool_height', 'tool_angle', 'tool_radius', 'tool_connection_diameter')
        }),
        ('Location', {
            'fields': ('row', 'column', 'table_id')
        }),
        ('Stock Information', {
            'fields': ('quantity',)
        }),
        ('System Fields', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Holder)
class HolderAdmin(admin.ModelAdmin):
    list_display = ('stock_code', 'product_code', 'holder_type', 'status', 'row', 'column')
    list_filter = ('holder_type', 'status', 'water_cooling', 'distance_cooling')
    search_fields = ('stock_code', 'product_code', 'description')
    ordering = ('stock_code',)
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('stock_code', 'product_code', 'supplier_name', 'holder_type', 'status', 'description')
        }),
        ('Pricing', {
            'fields': ('unit_price_tl', 'unit_price_euro', 'unit_price_usd')
        }),
        ('Holder Specifications', {
            'fields': ('holder_type_enum', 'pulley_type', 'water_cooling', 'distance_cooling', 'tool_connection_diameter')
        }),
        ('Location', {
            'fields': ('row', 'column', 'table_id')
        }),
        ('System Fields', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
