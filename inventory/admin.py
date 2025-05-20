from django.contrib import admin
from .models import (
    Product, RawMaterial, InventoryCategory, UnitOfMeasure, ProductBOM,
    TechnicalDrawing, StockTransaction, StockMovement, Tool, ToolUsage, # Added Tool, ToolUsage
    Holder, Fixture, ControlGauge # Tool removed
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

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'product_name', 'product_type', 'current_stock', 'reserved_stock', 'available_stock', 'inventory_category', 'customer', 'is_active')
    list_filter = ('product_type', 'inventory_category', 'is_active', 'customer')
    search_fields = ('product_code', 'product_name', 'description', 'project_name')
    readonly_fields = ('available_stock',)
    fieldsets = (
        (None, {
            'fields': ('product_code', 'product_name', 'project_name', 'product_type', 'multicode', 'description', 'is_active')
        }),
        ('Stock Information', {
            'fields': ('current_stock', 'reserved_stock', 'available_stock', 'unit_of_measure', 'inventory_category')
        }),
        ('Details', {
            'fields': ('customer',)
        }),
        ('Inventory Management', {
            'fields': ('reorder_point', 'lead_time_days', 'tags')
        }),
    )

@admin.register(InventoryCategory)
class InventoryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'unit_name', 'category')
    search_fields = ('unit_code', 'unit_name')
    list_filter = ('category',)

@admin.register(ProductBOM)
class ProductBOMAdmin(admin.ModelAdmin):
    list_display = ('parent_product', 'child_product', 'quantity', 'operation_sequence')
    list_filter = ('parent_product__product_code', 'child_product__product_code')
    search_fields = ('parent_product__product_code', 'child_product__product_code')

@admin.register(TechnicalDrawing)
class TechnicalDrawingAdmin(admin.ModelAdmin):
    list_display = ('drawing_code', 'product', 'version', 'effective_date', 'is_current', 'approved_by')
    list_filter = ('product__product_code', 'is_current', 'effective_date')
    search_fields = ('drawing_code', 'product__product_code', 'version')
    actions = ['mark_as_current', 'mark_as_not_current']

    def mark_as_current(self, request, queryset):
        queryset.update(is_current=True)
    mark_as_current.short_description = "Mark selected drawings as current"

    def mark_as_not_current(self, request, queryset):
        queryset.update(is_current=False)
    mark_as_not_current.short_description = "Mark selected drawings as not current"

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('get_item_display', 'transaction_type', 'quantity', 'category', 'transaction_date', 'created_by', 'reference')
    list_filter = ('transaction_type', 'category', 'transaction_date', 'product', 'raw_material')
    search_fields = ('product__product_code', 'raw_material__material_code', 'reference', 'notes')
    readonly_fields = ('created_by',) # 'transaction_date' could also be here

    def get_item_display(self, obj):
        if obj.product:
            return f"Product: {obj.product.product_code}"
        elif obj.raw_material:
            return f"Material: {obj.raw_material.material_code}"
        return "N/A"
    get_item_display.short_description = 'Item'

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('get_item_display', 'from_category', 'to_category', 'quantity', 'movement_date', 'created_by')
    list_filter = ('from_category', 'to_category', 'movement_date', 'product', 'raw_material')
    search_fields = ('product__product_code', 'raw_material__material_code', 'reference_id', 'notes')
    readonly_fields = ('created_by',)

    def get_item_display(self, obj):
        if obj.product:
            return f"Product: {obj.product.product_code}"
        elif obj.raw_material:
            return f"Material: {obj.raw_material.material_code}"
        return "N/A"
    get_item_display.short_description = 'Item'

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('stock_code', 'supplier_name', 'tool_type', 'status', 'quantity')
    list_filter = ('tool_type', 'status', 'supplier_name')
    search_fields = ('stock_code', 'supplier_name', 'product_code', 'tool_insert_code', 'description')

@admin.register(ToolUsage)
class ToolUsageAdmin(admin.ModelAdmin):
    list_display = ('tool', 'issued_date', 'returned_date', 'issued_by', 'condition_before', 'condition_after')
    list_filter = ('tool__stock_code', 'issued_by', 'condition_before', 'condition_after', 'issued_date')
    search_fields = ('tool__stock_code', 'notes')
    autocomplete_fields = ['tool', 'issued_by', 'returned_to']

@admin.register(Holder)
class HolderAdmin(admin.ModelAdmin):
    list_display = ('stock_code', 'supplier_name', 'holder_type', 'status')
    list_filter = ('holder_type', 'status', 'supplier_name', 'water_cooling', 'distance_cooling')
    search_fields = ('stock_code', 'supplier_name', 'product_code', 'description')

@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status')
    list_filter = ('status',)
    search_fields = ('code', 'name')

@admin.register(ControlGauge)
class ControlGaugeAdmin(admin.ModelAdmin):
    list_display = ('stock_code', 'stock_name', 'status', 'upcoming_calibration_date', 'current_location')
    list_filter = ('status', 'calibration_per_year', 'brand')
    search_fields = ('stock_code', 'stock_name', 'serial_number', 'brand', 'model', 'certificate_no', 'current_location')

