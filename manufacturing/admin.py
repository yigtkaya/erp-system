from django.contrib import admin
from .models import WorkOrder, Machine, BOM, BOMComponent, ManufacturingProcess, SubWorkOrder, WorkOrderOutput, BOMProcessConfig, SubWorkOrderProcess

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
    list_display = ('product', 'version', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('product__product_name', 'version')
    ordering = ('product__product_code', '-version')

@admin.register(BOMComponent)
class BOMComponentAdmin(admin.ModelAdmin):
    list_display = ('bom', 'component_type', 'get_item', 'quantity')
    list_filter = ('component_type', 'bom__product')
    
    def get_item(self, obj):
        if obj.component_type == 'PROCESS': return obj.process
        if obj.component_type == 'SEMI': return obj.product
        if obj.component_type == 'STANDARD': return obj.standard_part
        if obj.component_type == 'RAW': return obj.raw_material
        return '-'
    get_item.short_description = 'Component Item'

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
    list_display = ('process', 'machine_type', 'estimated_duration_minutes')
    list_filter = ('machine_type',)
    search_fields = ('process__process_name',)

@admin.register(SubWorkOrderProcess)
class SubWorkOrderProcessAdmin(admin.ModelAdmin):
    list_display = ('sub_work_order', 'process', 'machine', 'sequence_order', 'planned_duration_minutes')
    list_filter = ('machine__machine_type',)
    search_fields = ('sub_work_order__parent_work_order__order_number', 'process__process_name')
    ordering = ('sequence_order',)
