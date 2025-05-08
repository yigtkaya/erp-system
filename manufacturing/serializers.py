# manufacturing/serializers.py
from rest_framework import serializers
from .models import (
    ProductionLine, WorkCenter, WorkOrder, WorkOrderOperation,
    MaterialAllocation, ProductionOutput, MachineDowntime
)
from inventory.serializers import ProductSerializer
from core.serializers import UserListSerializer


class ProductionLineSerializer(serializers.ModelSerializer):
    work_center_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductionLine
        fields = [
            'id', 'code', 'name', 'description', 'is_active',
            'capacity_per_hour', 'work_center_count', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_work_center_count(self, obj):
        return obj.work_centers.count()


class WorkCenterSerializer(serializers.ModelSerializer):
    production_line = ProductionLineSerializer(read_only=True)
    production_line_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductionLine.objects.all(),
        source='production_line',
        write_only=True
    )
    
    class Meta:
        model = WorkCenter
        fields = [
            'id', 'code', 'name', 'description', 'production_line',
            'production_line_id', 'capacity_per_hour', 'setup_time_minutes',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class WorkOrderOperationSerializer(serializers.ModelSerializer):
    work_center = WorkCenterSerializer(read_only=True)
    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenter.objects.all(),
        source='work_center',
        write_only=True
    )
    assigned_to = UserListSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = WorkOrderOperation
        fields = [
            'id', 'work_order', 'operation_sequence', 'operation_name',
            'work_center', 'work_center_id', 'planned_start_date',
            'planned_end_date', 'actual_start_date', 'actual_end_date',
            'setup_time_minutes', 'run_time_minutes', 'quantity_completed',
            'quantity_scrapped', 'status', 'assigned_to', 'assigned_to_id',
            'notes', 'created_at'
        ]
        read_only_fields = ['created_at']


class MaterialAllocationSerializer(serializers.ModelSerializer):
    material = ProductSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='material',
        write_only=True
    )
    
    class Meta:
        model = MaterialAllocation
        fields = [
            'id', 'work_order', 'material', 'material_id',
            'required_quantity', 'allocated_quantity', 'consumed_quantity',
            'is_allocated', 'allocation_date', 'allocation_percentage'
        ]
        read_only_fields = ['allocation_percentage']


class WorkOrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    work_center = WorkCenterSerializer(read_only=True)
    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenter.objects.all(),
        source='work_center',
        write_only=True
    )
    operations = WorkOrderOperationSerializer(many=True, read_only=True)
    material_allocations = MaterialAllocationSerializer(many=True, read_only=True)
    completion_percentage = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkOrder
        fields = [
            'id', 'work_order_number', 'product', 'product_id',
            'quantity_ordered', 'quantity_completed', 'quantity_scrapped',
            'planned_start_date', 'planned_end_date', 'actual_start_date',
            'actual_end_date', 'status', 'priority', 'work_center',
            'work_center_id', 'sales_order', 'notes', 'operations',
            'material_allocations', 'completion_percentage', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductionOutputSerializer(serializers.ModelSerializer):
    work_order = serializers.PrimaryKeyRelatedField(read_only=True)
    operation = serializers.PrimaryKeyRelatedField(read_only=True)
    operator = UserListSerializer(read_only=True)
    
    class Meta:
        model = ProductionOutput
        fields = [
            'id', 'work_order', 'operation', 'quantity_good',
            'quantity_scrapped', 'output_date', 'operator',
            'batch_number', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']


class MachineDowntimeSerializer(serializers.ModelSerializer):
    work_center = WorkCenterSerializer(read_only=True)
    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenter.objects.all(),
        source='work_center',
        write_only=True
    )
    reported_by = UserListSerializer(read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = MachineDowntime
        fields = [
            'id', 'work_center', 'work_center_id', 'start_time',
            'end_time', 'reason', 'category', 'notes', 'reported_by',
            'duration_minutes', 'created_at'
        ]
        read_only_fields = ['created_at', 'reported_by']