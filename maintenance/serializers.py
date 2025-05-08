# maintenance/serializers.py
from rest_framework import serializers
from .models import (
    Equipment, MaintenancePlan, WorkOrder, MaintenanceTask,
    SparePart, MaintenancePartUsage, MaintenanceLog
)
from core.serializers import UserListSerializer
from manufacturing.serializers import WorkCenterSerializer
from purchasing.serializers import SupplierSerializer


class EquipmentSerializer(serializers.ModelSerializer):
    work_center = WorkCenterSerializer(read_only=True)
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


class MaintenancePlanSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    
    class Meta:
        model = MaintenancePlan
        fields = [
            'id', 'equipment', 'equipment_id', 'plan_name',
            'maintenance_type', 'frequency_days', 'next_due_date',
            'estimated_duration_hours', 'instructions', 'is_active'
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


class SparePartSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
        write_only=True,
        required=False
    )
    equipment = EquipmentSerializer(many=True, read_only=True)
    is_below_minimum = serializers.ReadOnlyField()
    
    class Meta:
        model = SparePart
        fields = [
            'id', 'part_number', 'name', 'description', 'equipment',
            'minimum_stock', 'current_stock', 'unit_cost', 'supplier',
            'supplier_id', 'location', 'is_below_minimum'
        ]


class MaintenancePartUsageSerializer(serializers.ModelSerializer):
    spare_part = SparePartSerializer(read_only=True)
    spare_part_id = serializers.PrimaryKeyRelatedField(
        queryset=SparePart.objects.all(),
        source='spare_part',
        write_only=True
    )
    total_cost = serializers.ReadOnlyField()
    
    class Meta:
        model = MaintenancePartUsage
        fields = [
            'id', 'work_order', 'spare_part', 'spare_part_id',
            'quantity_used', 'unit_cost', 'total_cost', 'notes'
        ]


class WorkOrderSerializer(serializers.ModelSerializer):
    equipment = EquipmentSerializer(read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    maintenance_plan = MaintenancePlanSerializer(read_only=True)
    assigned_to = UserListSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True
    )
    reported_by = UserListSerializer(read_only=True)
    tasks = MaintenanceTaskSerializer(many=True, read_only=True)
    parts_used = MaintenancePartUsageSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkOrder
        fields = [
            'id', 'work_order_number', 'equipment', 'equipment_id',
            'maintenance_plan', 'maintenance_type', 'priority', 'status',
            'description', 'scheduled_start', 'scheduled_end',
            'actual_start', 'actual_end', 'assigned_to', 'assigned_to_id',
            'reported_by', 'estimated_hours', 'actual_hours', 'notes',
            'tasks', 'parts_used', 'is_overdue'
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