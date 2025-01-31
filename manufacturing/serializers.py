from rest_framework import serializers
from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput
)
from inventory.serializers import InventoryCategorySerializer

class BOMComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMComponent
        fields = [
            'id', 'bom', 'component_type', 'semi_product', 
            'raw_material', 'process_config', 'quantity',
            'sequence_order'
        ]

class BOMSerializer(serializers.ModelSerializer):
    components = BOMComponentSerializer(many=True, read_only=True)
    
    class Meta:
        model = BOM
        fields = [
            'id', 'product', 'version', 'is_active',
            'components', 'created_at', 'modified_at'
        ]

class WorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = [
            'id', 'order_number', 'sales_order_item', 'bom',
            'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status', 'priority',
            'notes', 'created_at', 'modified_at'
        ]

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = [
            'id', 'machine_code', 'machine_type', 'status',
            'brand', 'model', 'axis_count', 'internal_cooling',
            'motor_power_kva', 'holder_type', 'spindle_speed_rpm',
            'tool_count', 'nc_control_unit', 'manufacturing_year',
            'serial_number', 'machine_weight_kg', 'max_part_size',
            'description', 'created_at', 'modified_at'
        ]

class ManufacturingProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturingProcess
        fields = [
            'id', 'process_code', 'process_name',
            'standard_time_minutes', 'machine_type',
            'approved_by', 'created_at', 'modified_at'
        ]

class SubWorkOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubWorkOrder
        fields = [
            'id', 'parent_work_order', 'bom_component',
            'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status',
            'output_quantity', 'scrap_quantity',
            'target_category', 'notes', 'created_at',
            'modified_at'
        ]

class WorkOrderOutputSerializer(serializers.ModelSerializer):
    target_category = InventoryCategorySerializer(read_only=True)
    
    class Meta:
        model = WorkOrderOutput
        fields = [
            'id', 'sub_work_order', 'quantity', 'status',
            'target_category', 'notes', 'created_at',
            'modified_at'
        ] 