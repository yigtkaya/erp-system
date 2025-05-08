# manufacturing/admin.py
from django.contrib import admin
from .models import (
    ProductionLine, WorkCenter, WorkOrder, WorkOrderOperation,
    MaterialAllocation, ProductionOutput, MachineDowntime,
    ManufacturingProcess, ProductWorkflow, ProcessConfig,
    Fixture, ControlGauge, SubWorkOrder
)

@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'capacity_per_hour', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('is_active',)

@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'production_line', 'capacity_per_hour', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('production_line', 'is_active')

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order_number', 'product', 'quantity_ordered', 'quantity_completed', 
                   'status', 'priority', 'planned_start_date', 'work_center')
    search_fields = ('work_order_number', 'product__product_code', 'product__name')
    list_filter = ('status', 'priority', 'work_center')
    date_hierarchy = 'planned_start_date'

@admin.register(WorkOrderOperation)
class WorkOrderOperationAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'operation_sequence', 'operation_name', 'work_center', 
                   'status', 'planned_start_date')
    search_fields = ('operation_name', 'work_order__work_order_number')
    list_filter = ('status', 'work_center')
    date_hierarchy = 'planned_start_date'

@admin.register(MaterialAllocation)
class MaterialAllocationAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'material', 'required_quantity', 'allocated_quantity', 
                   'consumed_quantity', 'is_allocated')
    search_fields = ('work_order__work_order_number', 'material__product_code')
    list_filter = ('is_allocated',)

@admin.register(ProductionOutput)
class ProductionOutputAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'quantity_good', 'quantity_scrapped', 
                   'output_date', 'operator')
    search_fields = ('work_order__work_order_number',)
    list_filter = ('output_date',)
    date_hierarchy = 'output_date'

@admin.register(MachineDowntime)
class MachineDowntimeAdmin(admin.ModelAdmin):
    list_display = ('work_center', 'start_time', 'end_time', 'reason', 'category')
    search_fields = ('work_center__code', 'reason')
    list_filter = ('category', 'work_center')
    date_hierarchy = 'start_time'

# Admin registrations for new models
@admin.register(ManufacturingProcess)
class ManufacturingProcessAdmin(admin.ModelAdmin):
    list_display = ('process_code', 'name', 'machine_type', 'standard_setup_time', 'standard_runtime')
    search_fields = ('process_code', 'name', 'machine_type')
    list_filter = ('machine_type',)

@admin.register(ProductWorkflow)
class ProductWorkflowAdmin(admin.ModelAdmin):
    list_display = ('product', 'version', 'status', 'effective_date', 'approved_by')
    search_fields = ('product__product_code', 'version')
    list_filter = ('status', 'effective_date')
    date_hierarchy = 'effective_date'

@admin.register(ProcessConfig)
class ProcessConfigAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'process', 'sequence_order', 'version', 'status')
    search_fields = ('workflow__product__product_code', 'process__name')
    list_filter = ('status', 'axis_count')

@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'fixture_type', 'status', 'location', 'next_check_date')
    search_fields = ('code', 'name', 'location')
    list_filter = ('status', 'fixture_type')
    date_hierarchy = 'next_check_date'

@admin.register(ControlGauge)
class ControlGaugeAdmin(admin.ModelAdmin):
    list_display = ('code', 'stock_name', 'status', 'calibration_date', 'upcoming_calibration_date')
    search_fields = ('code', 'stock_name')
    list_filter = ('status',)
    date_hierarchy = 'upcoming_calibration_date'

@admin.register(SubWorkOrder)
class SubWorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order_number', 'parent_work_order', 'status', 
                   'quantity_ordered', 'completion_percentage', 'planned_start')
    search_fields = ('work_order_number', 'parent_work_order__work_order_number')
    list_filter = ('status', 'target_category')
    date_hierarchy = 'planned_start'