from django.contrib import admin
from .models import (
    WorkOrder, Machine, BOM, BOMComponent, ManufacturingProcess, 
    SubWorkOrder, WorkOrderOutput, SubWorkOrderProcess, WorkflowProcess,
    ProcessConfig
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
    list_display = ('bom', 'product', 'quantity', 'sequence_order')
    list_filter = ('bom__product__product_type',)
    search_fields = ('product__product_code', 'product__product_name', 'notes')
    raw_id_fields = ('bom', 'product')
    fieldsets = (
        (None, {
            'fields': ('bom', 'sequence_order', 'quantity', 'product')
        }),
        ('Additional Information', {
            'fields': ('lead_time_days', 'notes'),
            'classes': ('collapse',)
        }),
    )

@admin.register(WorkflowProcess)
class WorkflowProcessAdmin(admin.ModelAdmin):
    list_display = ('product', 'process', 'stock_code', 'sequence_order')
    list_filter = ('product__product_type',)
    search_fields = (
        'stock_code',
        'product__product_name',
        'process__process_name'
    )
    ordering = ('product', 'sequence_order')
    fieldsets = (
        (None, {
            'fields': ('product', 'process', 'stock_code', 'sequence_order')
        }),
    )

@admin.register(ManufacturingProcess)
class ManufacturingProcessAdmin(admin.ModelAdmin):
    list_display = ('process_code', 'process_name')
    search_fields = ('process_code', 'process_name')
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
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'production_date'),
            'classes': ('collapse',)
        })
    )

@admin.register(SubWorkOrderProcess)
class SubWorkOrderProcessAdmin(admin.ModelAdmin):
    list_display = ('sub_work_order', 'workflow_process', 'process_config', 'machine', 'status', 'sequence_order')
    list_filter = ('status', 'machine__machine_type')
    search_fields = (
        'sub_work_order__parent_work_order__order_number',
        'workflow_process__process_number',
        'workflow_process__process__process_name'
    )
    ordering = ('sequence_order',)
    fieldsets = (
        (None, {
            'fields': ('sub_work_order', 'workflow_process', 'process_config', 'sequence_order')
        }),
        ('Machine & Operator', {
            'fields': ('machine', 'operator', 'setup_time_minutes')
        }),
        ('Timing', {
            'fields': ('planned_duration_minutes', 'actual_duration_minutes', 'start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        })
    )

@admin.register(ProcessConfig)
class ProcessConfigAdmin(admin.ModelAdmin):
    list_display = (
        'workflow_process', 
        'axis_count', 
        'tool',
        'control_gauge',
        'fixture',
        'get_cycle_time'
    )
    list_filter = (
        'axis_count',
        ('tool', admin.RelatedOnlyFieldListFilter),
        ('control_gauge', admin.RelatedOnlyFieldListFilter),
        ('fixture', admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        'workflow_process__product__product_name',
        'workflow_process__process__process_name',
        'workflow_process__stock_code',
        'tool__stock_code',
        'control_gauge__stock_code',
        'fixture__stock_code'
    )
    raw_id_fields = ('workflow_process', 'tool', 'control_gauge', 'fixture')
    fieldsets = (
        (None, {
            'fields': ('workflow_process',)
        }),
        ('Equipment Requirements', {
            'fields': (
                'axis_count',
                'tool',
                'control_gauge',
                'fixture',
                'number_of_bindings'
            )
        }),
        ('Time Requirements', {
            'fields': (
                'setup_time',
                'machine_time',
                'net_time'
            ),
            'description': 'All times are in minutes. Cycle time is calculated as: Machine Time + max(Setup Time, Net Time), divided by number of bindings if applicable.'
        })
    )

    def get_cycle_time(self, obj):
        return f"{obj.get_cycle_time():.2f}"
    get_cycle_time.short_description = 'Cycle Time (min)'
