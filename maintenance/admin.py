# maintenance/admin.py
from django.contrib import admin
# The models below don't exist yet - they will be implemented later
"""
from .models import (
    Equipment, MaintenancePlan, WorkOrder, MaintenanceTask,
    SparePart, MaintenancePartUsage, MaintenanceLog
)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'manufacturer', 'is_active')
    search_fields = ('code', 'name', 'serial_number')
    list_filter = ('is_active',)

@admin.register(MaintenancePlan)
class MaintenancePlanAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'plan_name', 'maintenance_type', 'frequency_days', 'next_due_date')
    search_fields = ('plan_name', 'equipment__name')
    list_filter = ('maintenance_type', 'is_active')
    date_hierarchy = 'next_due_date'

@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('work_order_number', 'equipment', 'maintenance_type', 'priority', 'status')
    search_fields = ('work_order_number', 'equipment__name')
    list_filter = ('maintenance_type', 'priority', 'status')
    date_hierarchy = 'scheduled_start'

@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ('part_number', 'name', 'current_stock', 'minimum_stock', 'unit_cost')
    search_fields = ('part_number', 'name')
    list_filter = ('supplier',)

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'log_type', 'log_date', 'logged_by')
    search_fields = ('description', 'action_taken')
    list_filter = ('log_type', 'equipment')
    date_hierarchy = 'log_date'
"""