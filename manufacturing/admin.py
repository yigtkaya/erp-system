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
    list_display = ('bom', 'product', 'sequence_order', 'quantity', 'created_by', 'modified_by')
    list_filter = ('bom__product__product_type', 'product__product_type', 'created_by', 'modified_by')
    search_fields = ('bom__product__product_name', 'product__product_name')
    ordering = ('bom', 'sequence_order')
    readonly_fields = ('created_by', 'modified_by', 'created_at', 'modified_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('bom', 'product', 'sequence_order', 'quantity')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'modified_by', 'created_at', 'modified_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProcessComponent)
class ProcessComponentAdmin(admin.ModelAdmin):
    list_display = ('bom', 'process_config', 'raw_material', 'sequence_order', 'get_quantity', 'created_by', 'modified_by')
    list_filter = ('process_config__process__machine_type', 'created_by', 'modified_by')
    search_fields = ('bom__product__product_name', 'process_config__process__process_name')
    ordering = ('bom', 'sequence_order')
    readonly_fields = ('created_by', 'modified_by', 'created_at', 'modified_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('bom', 'process_config', 'sequence_order')
        }),
        ('Optional Information', {
            'fields': ('quantity', 'raw_material', 'notes'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'modified_by', 'created_at', 'modified_at'),
            'classes': ('collapse',)
        })
    )

    def get_quantity(self, obj):
        return obj.quantity if obj.quantity is not None else 'Not specified'
    get_quantity.short_description = 'Quantity'

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
    list_display = ('sub_work_order', 'quantity', 'status', 'target_category', 'inspection_required')
    list_filter = ('status', 'target_category', 'inspection_required')
    search_fields = ('sub_work_order__parent_work_order__order_number', 'quarantine_reason', 'notes')
    ordering = ('-created_at',)
    readonly_fields = ('inspection_required',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('sub_work_order', 'quantity', 'status', 'target_category')
        }),
        ('Quality Control', {
            'fields': ('inspection_required', 'quarantine_reason'),
            'classes': ('collapse',),
            'description': 'Quality control and quarantine information'
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )

@admin.register(BOMProcessConfig)
class BOMProcessConfigAdmin(admin.ModelAdmin):
    list_display = ('process', 'get_axis_count', 'get_duration')
    list_filter = ('process__machine_type',)
    search_fields = ('process__process_name', 'process__process_code')
    fieldsets = (
        ('Process Information', {
            'fields': ('process',)
        }),
        ('Configuration', {
            'fields': ('axis_count', 'estimated_duration_minutes'),
            'classes': ('collapse',),
            'description': 'Optional configuration settings for the process'
        }),
        ('Requirements', {
            'fields': ('tooling_requirements', 'quality_checks'),
            'classes': ('collapse',),
            'description': 'Optional tooling and quality requirements'
        })
    )

    def get_axis_count(self, obj):
        return obj.axis_count if obj.axis_count else 'Not specified'
    get_axis_count.short_description = 'Axis Count'

    def get_duration(self, obj):
        return f"{obj.estimated_duration_minutes} minutes" if obj.estimated_duration_minutes else 'Not specified'
    get_duration.short_description = 'Estimated Duration'

@admin.register(SubWorkOrderProcess)
class SubWorkOrderProcessAdmin(admin.ModelAdmin):
    list_display = ('sub_work_order', 'process', 'machine', 'sequence_order', 'planned_duration_minutes')
    list_filter = ('machine__machine_type',)
    search_fields = ('sub_work_order__parent_work_order__order_number', 'process__process_name')
    ordering = ('sequence_order',)
