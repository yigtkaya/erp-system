# maintenance/serializers.py
from rest_framework import serializers
from .models import (
    Equipment, MaintenanceWorkOrder, MaintenanceTask,
    MaintenanceLog
)
from core.serializers import UserListSerializer
from manufacturing.serializers import WorkCenterSerializer
from purchasing.serializers import SupplierSerializer

# Imports to be added
from manufacturing.models import WorkCenter
from core.models import User # Assuming User is from core.models as per models.py


class EquipmentSerializer(serializers.ModelSerializer):
    work_center_display = WorkCenterSerializer(source='work_center', read_only=True)
    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenter.objects.all(),
        source='work_center',
        write_only=True
    )
    
    class Meta:
        model = Equipment
        fields = [
            'id', 'code', 'name', 'description', 'work_center',
            'work_center_id', 'manufacturer', 'model_number',
            'serial_number', 'purchase_date', 'warranty_expiry',
            'is_active', 'specifications'
        ]


class MaintenanceTaskSerializer(serializers.ModelSerializer):
    completed_by = UserListSerializer(read_only=True)
    
    class Meta:
        model = MaintenanceTask
        fields = [
            'id', 'work_order', 'task_name', 'description',
            'sequence_number', 'estimated_hours', 'actual_hours',
            'is_completed', 'completed_by', 'completed_at', 'notes'
        ]


class WorkOrderSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    assigned_to = UserListSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True
    )
    reported_by = UserListSerializer(read_only=True)
    tasks = MaintenanceTaskSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = MaintenanceWorkOrder
        fields = [
            'id', 'work_order_number', 'equipment', 'equipment_id',
            'maintenance_type', 'priority', 'status',
            'description', 'scheduled_start', 'scheduled_end',
            'actual_start', 'actual_end', 'assigned_to', 'assigned_to_id',
            'reported_by', 'estimated_hours', 'actual_hours', 'notes',
            'tasks', 'is_overdue'
        ]
        read_only_fields = ['reported_by']


class MaintenanceLogSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    work_order = WorkOrderSerializer(read_only=True)
    logged_by = UserListSerializer(read_only=True)
    
    class Meta:
        model = MaintenanceLog
        fields = [
            'id', 'equipment', 'equipment_id', 'work_order', 'log_type',
            'description', 'action_taken', 'logged_by', 'log_date',
            'downtime_hours'
        ]
        read_only_fields = ['logged_by']