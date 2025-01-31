from django.contrib import admin
from .models import Maintenance, FaultReport

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('machine', 'maintenance_type', 'scheduled_date', 'status', 'assigned_to')
    list_filter = ('maintenance_type', 'status', 'machine__machine_type')
    search_fields = ('machine__machine_code', 'notes')
    date_hierarchy = 'scheduled_date'

@admin.register(FaultReport)
class FaultReportAdmin(admin.ModelAdmin):
    list_display = ('machine', 'severity', 'status', 'reported_by', 'created_at')
    list_filter = ('severity', 'status', 'machine__machine_type')
    search_fields = ('machine__machine_code', 'fault_description')
    raw_id_fields = ('machine', 'reported_by', 'resolved_by')
