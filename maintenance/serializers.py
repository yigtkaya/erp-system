# maintenance/serializers.py
from rest_framework import serializers
from .models import (
    Equipment, MaintenanceWorkOrder, MaintenanceTask,
    MaintenanceLog
)
from core.serializers import UserListSerializer
from core.models import User


class EquipmentSerializer(serializers.ModelSerializer):
    
    
    class Meta:
        model = Equipment
        fields = [
            'id', 'code', 'name', 'description', 'model', 'serial_number',
            'manufacturer', 'purchase_date', 'warranty_end_date', 'status',
            'location',
            'parent_equipment', 'maintenance_interval_days', 'last_maintenance_date',
            'next_maintenance_date', 'created_at', 'updated_at'
        ]


class MaintenanceTaskSerializer(serializers.ModelSerializer):
    assigned_to_display = UserListSerializer(source='assigned_to', read_only=True)
    
    class Meta:
        model = MaintenanceTask
        fields = [
            'id', 'work_order', 'task_description', 'detailed_instructions',
            'estimated_hours', 'actual_hours', 'assigned_to', 'assigned_to_display',
            'status', 'completion_date', 'requires_parts'
        ]


class WorkOrderSerializer(serializers.ModelSerializer):
    equipment_display = EquipmentSerializer(source='equipment', read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    assigned_to_display = UserListSerializer(source='assigned_to', read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True,
        required=False
    )
    reported_by_display = UserListSerializer(source='reported_by', read_only=True)
    tasks = MaintenanceTaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = MaintenanceWorkOrder
        fields = [
            'id', 'work_order_number', 'equipment', 'equipment_id', 'equipment_display',
            'maintenance_type', 'description', 'reported_by', 'reported_by_display',
            'assigned_to', 'assigned_to_id', 'assigned_to_display', 'priority', 'status',
            'planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date',
            'total_downtime_hours', 'schedule', 'tasks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reported_by']


class MaintenanceLogSerializer(serializers.ModelSerializer):
    equipment_display = EquipmentSerializer(source='equipment', read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    work_order_display = WorkOrderSerializer(source='work_order', read_only=True)
    performed_by_display = UserListSerializer(source='performed_by', read_only=True)
    
    class Meta:
        model = MaintenanceLog
        fields = [
            'id', 'equipment', 'equipment_id', 'equipment_display', 'work_order', 'work_order_display',
            'maintenance_type', 'maintenance_date', 'performed_by', 'performed_by_display',
            'description', 'hours_spent', 'cost', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['performed_by']