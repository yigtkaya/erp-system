from django.contrib import admin
from .models import (
    WorkOrder, Machine, BOM, BOMComponent, ManufacturingProcess, 
    SubWorkOrder, WorkOrderOutput, BOMProcessConfig, SubWorkOrderProcess,
    ProductComponent, ProcessComponent
)

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'bom', 'quantity', 'status', 'planned_start', 'planned_end')
    list_filter = ('status', 'planned_start', 'planned_end')
    search_fields = ('order_number', 'bom__product__product_name', 'notes')
    ordering = ('-created_at',)
    date_hierarchy = 'planned_start'

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('machine_code', 'machine_type', 'status', 'brand', 'model')
    list_filter = ('machine_type', 'status', 'internal_cooling')
    search_fields = ('machine_code', 'brand', 'model', 'description')
    ordering = ('machine_code',)

@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ('product', 'version', 'is_active', 'get_product_type')
    list_filter = ('is_active', 'product__product_type')
    search_fields = ('product__product_name', 'version')
    ordering = ('product__product_code', '-version')

    def get_product_type(self, obj):
        return obj.product.get_product_type_display()
    get_product_type.short_description = 'Product Type'

@admin.register(BOMComponent)
class BOMComponentAdmin(admin.ModelAdmin):
    list_display = ('bom', 'sequence_order', 'quantity')
    list_filter = ('bom__product__product_type',)
    search_fields = ('bom__product__product_name',)
    ordering = ('bom', 'sequence_order')

@admin.register(ProductComponent)
class ProductComponentAdmin(admin.ModelAdmin):
    list_display = ('bom', 'product', 'sequence_order', 'quantity')
    list_filter = ('bom__product__product_type', 'product__product_type')
    search_fields = ('bom__product__product_name', 'product__product_name')
    ordering = ('bom', 'sequence_order')

@admin.register(ProcessComponent)
class ProcessComponentAdmin(admin.ModelAdmin):
    list_display = ('bom', 'process_config', 'raw_material', 'sequence_order', 'quantity')
    list_filter = ('process_config__process__machine_type',)
    search_fields = ('bom__product__product_name', 'process_config__process__process_name')
    ordering = ('bom', 'sequence_order')

@admin.register(ManufacturingProcess)
class ManufacturingProcessAdmin(admin.ModelAdmin):
    list_display = ('process_code', 'process_name', 'standard_time_minutes', 'machine_type')
    search_fields = ('process_code', 'process_name')
    list_filter = ('machine_type',)
    ordering = ('process_code',)

@admin.register(SubWorkOrder)
class SubWorkOrderAdmin(admin.ModelAdmin):
    list_display = ('parent_work_order', 'bom_component', 'status', 'planned_start', 'planned_end')
    list_filter = ('status', 'planned_start', 'planned_end')
    search_fields = ('parent_work_order__order_number',)
    ordering = ('-created_at',)

@admin.register(WorkOrderOutput)
class WorkOrderOutputAdmin(admin.ModelAdmin):
    list_display = ('sub_work_order', 'quantity', 'status', 'target_category')
    list_filter = ('status', 'target_category')
    search_fields = ('sub_work_order__parent_work_order__order_number',)
    ordering = ('-created_at',)

@admin.register(BOMProcessConfig)
class BOMProcessConfigAdmin(admin.ModelAdmin):
    list_display = ('process', 'axis_count', 'estimated_duration_minutes')
    list_filter = ('axis_count',)
    search_fields = ('process__process_name',)

@admin.register(SubWorkOrderProcess)
class SubWorkOrderProcessAdmin(admin.ModelAdmin):
    list_display = ('sub_work_order', 'process', 'machine', 'sequence_order', 'planned_duration_minutes')
    list_filter = ('machine__machine_type',)
    search_fields = ('sub_work_order__parent_work_order__order_number', 'process__process_name')
    ordering = ('sequence_order',)
