from django.contrib import admin
from .models import (
    ManufacturingProcess, Machine, ProductWorkflow, ProcessConfig,
    WorkOrder, SubWorkOrder, SubWorkOrderProcess, WorkOrderOutput,
    BOM, BOMComponent
)

@admin.register(ManufacturingProcess)
class ManufacturingProcessAdmin(admin.ModelAdmin):
    list_display = ['process_code', 'process_name']
    search_fields = ['process_code', 'process_name']
    ordering = ['process_code']

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ['machine_code', 'machine_type', 'status', 'axis_count']
    list_filter = ['machine_type', 'status', 'axis_count']
    search_fields = ['machine_code', 'brand', 'model']
    ordering = ['machine_code']

class ProcessConfigInline(admin.TabularInline):
    model = ProcessConfig
    extra = 0
    fields = [
        'process', 'version', 'status', 'sequence_order', 'stock_code',
        'tool', 'control_gauge', 'fixture', 'axis_count'
    ]
    ordering = ['sequence_order']

@admin.register(ProductWorkflow)
class ProductWorkflowAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'version', 'status', 'effective_date',
        'created_by', 'approved_by'
    ]
    list_filter = ['status', 'effective_date']
    search_fields = ['product__product_code', 'product__product_name', 'version']
    ordering = ['product', '-version']
    inlines = [ProcessConfigInline]
    readonly_fields = ['effective_date', 'approved_by', 'approved_at']

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ProcessConfig)
class ProcessConfigAdmin(admin.ModelAdmin):
    list_display = [
        'workflow', 'process', 'version', 'status',
        'sequence_order', 'stock_code'
    ]
    list_filter = ['status', 'axis_count']
    search_fields = [
        'workflow__product__product_code',
        'process__process_code',
        'stock_code'
    ]
    ordering = ['workflow', 'sequence_order']
    readonly_fields = ['effective_date']

class SubWorkOrderProcessInline(admin.TabularInline):
    model = SubWorkOrderProcess
    extra = 0
    fields = [
        'process_config', 'machine', 'sequence_order',
        'planned_duration_minutes', 'status'
    ]

class WorkOrderOutputInline(admin.TabularInline):
    model = WorkOrderOutput
    extra = 0
    fields = [
        'quantity', 'status', 'target_category',
        'inspection_required', 'production_date'
    ]

@admin.register(SubWorkOrder)
class SubWorkOrderAdmin(admin.ModelAdmin):
    list_display = [
        'parent_work_order', 'bom_component',
        'quantity', 'status', 'completion_percentage'
    ]
    list_filter = ['status']
    search_fields = [
        'parent_work_order__order_number',
        'bom_component__product__product_code'
    ]
    inlines = [SubWorkOrderProcessInline, WorkOrderOutputInline]
    readonly_fields = ['completion_percentage']

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'bom', 'quantity',
        'status', 'priority', 'completion_percentage'
    ]
    list_filter = ['status', 'priority']
    search_fields = [
        'order_number',
        'bom__product__product_code',
        'sales_order_item__sales_order__order_number'
    ]
    readonly_fields = ['completion_percentage']

@admin.register(WorkOrderOutput)
class WorkOrderOutputAdmin(admin.ModelAdmin):
    list_display = [
        'sub_work_order', 'quantity',
        'status', 'target_category', 'production_date'
    ]
    list_filter = ['status', 'target_category', 'production_date']
    search_fields = [
        'sub_work_order__parent_work_order__order_number',
        'sub_work_order__bom_component__product__product_code'
    ]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class BOMComponentInline(admin.TabularInline):
    """
    Inline admin for BOM components allowing editing components directly in the BOM admin.
    """
    model = BOMComponent
    extra = 1  # Show one empty form for adding new components
    fields = [
        'sequence_order', 'product', 'quantity',
        'notes'
    ]
    ordering = ['sequence_order']
    autocomplete_fields = ['product']  # Enable autocomplete for product selection

@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'version', 'is_active', 'is_approved',
        'approved_by', 'created_at', 'modified_at'
    ]
    list_filter = ['is_active', 'is_approved', 'created_at']
    search_fields = [
        'product__product_code',
        'product__product_name',
        'version',
        'notes'
    ]
    readonly_fields = ['approved_by', 'approved_at', 'created_at', 'modified_at']
    autocomplete_fields = ['product', 'parent_bom']
    inlines = [BOMComponentInline]
    ordering = ['-created_at']

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:  # If new instance
                instance.created_by = request.user
            instance.modified_by = request.user
            instance.save()
        formset.save_m2m()
        # Handle deletions
        for obj in formset.deleted_objects:
            obj.delete()

@admin.register(BOMComponent)
class BOMComponentAdmin(admin.ModelAdmin):
    list_display = [
        'bom', 'sequence_order', 'product',
        'quantity'
    ]
    list_filter = ['bom__is_active', 'bom__is_approved']
    search_fields = [
        'bom__product__product_code',
        'product__product_code',
        'notes'
    ]
    autocomplete_fields = ['bom', 'product']
    ordering = ['bom', 'sequence_order']

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)
