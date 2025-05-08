# manufacturing/admin.py
from django.contrib import admin
from .models import (
    ProductionLine, WorkCenter, WorkOrder, WorkOrderOperation,
    MaterialAllocation, ProductionOutput, MachineDowntime
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
    list_display = ('work_order_number', 'product', 'quantity_ordered', 'status', 'priority')
    search_fields = ('work_order_number', 'product__product_code')
    list_filter = ('status', 'priority', 'created_at')
    date_hierarchy = 'created_at'

@admin.register(WorkOrderOperation)
class WorkOrderOperationAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'operation_sequence', 'operation_name', 'status')
    list_filter = ('status',)

@admin.register(ProductionOutput)
class ProductionOutputAdmin(admin.ModelAdmin):
    list_display = ('work_order', 'quantity_good', 'quantity_scrapped', 'output_date', 'operator')
    date_hierarchy = 'output_date'

@admin.register(MachineDowntime)
class MachineDowntimeAdmin(admin.ModelAdmin):
    list_display = ('work_center', 'start_time', 'end_time', 'reason', 'category')
    list_filter = ('category', 'work_center')
    date_hierarchy = 'start_time'