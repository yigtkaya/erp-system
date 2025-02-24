from rest_framework import serializers
from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput, BOMProcessConfig,
    ProcessComponent, ProductComponent, SubWorkOrderProcess
)
from inventory.serializers import InventoryCategorySerializer, ProductSerializer, RawMaterialSerializer

class ManufacturingProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturingProcess
        fields = [
            'id', 'process_code', 'process_name',
            'standard_time_minutes', 'machine_type',
            'approved_by', 'created_at', 'modified_at'
        ]

class BOMProcessConfigSerializer(serializers.ModelSerializer):
    process_name = serializers.CharField(source='process.process_name', read_only=True)
    process_code = serializers.CharField(source='process.process_code', read_only=True)
    machine_type = serializers.CharField(source='process.machine_type', read_only=True)

    class Meta:
        model = BOMProcessConfig
        fields = [
            'id', 'process', 'process_name', 'process_code',
            'machine_type', 'axis_count', 'estimated_duration_minutes',
            'tooling_requirements', 'quality_checks'
        ]
        extra_kwargs = {
            'axis_count': {'required': False},
            'estimated_duration_minutes': {'required': False},
            'tooling_requirements': {'required': False},
            'quality_checks': {'required': False}
        }

    def validate_estimated_duration_minutes(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Estimated duration must be a positive number")
        return value

class ProcessComponentSerializer(serializers.ModelSerializer):
    process_config = BOMProcessConfigSerializer(read_only=True)
    raw_material = RawMaterialSerializer(read_only=True)

    class Meta:
        model = ProcessComponent
        fields = [
            'id', 'bom', 'sequence_order', 'quantity',
            'notes', 'process_config', 'raw_material'
        ]
        extra_kwargs = {
            'quantity': {'required': False}
        }

class ProductComponentSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductComponent
        fields = [
            'id', 'bom', 'sequence_order', 'quantity',
            'notes', 'product'
        ]
        extra_kwargs = {
            'quantity': {'required': True}
        }

class BOMComponentSerializer(serializers.ModelSerializer):
    process_component = ProcessComponentSerializer(read_only=True)
    product_component = ProductComponentSerializer(read_only=True)

    class Meta:
        model = BOMComponent
        fields = [
            'id', 'bom', 'sequence_order', 'quantity',
            'notes', 'process_component', 'product_component'
        ]

class BOMSerializer(serializers.ModelSerializer):
    components = BOMComponentSerializer(many=True, read_only=True)
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = BOM
        fields = [
            'id', 'product', 'version', 'is_active',
            'components', 'created_at', 'modified_at'
        ]

class SubWorkOrderProcessSerializer(serializers.ModelSerializer):
    process = ManufacturingProcessSerializer(read_only=True)
    machine = serializers.PrimaryKeyRelatedField(queryset=Machine.objects.all())

    class Meta:
        model = SubWorkOrderProcess
        fields = [
            'id', 'sub_work_order', 'process', 'machine',
            'sequence_order', 'planned_duration_minutes',
            'actual_duration_minutes'
        ]

class SubWorkOrderSerializer(serializers.ModelSerializer):
    processes = SubWorkOrderProcessSerializer(many=True, read_only=True)
    outputs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    target_category = InventoryCategorySerializer(read_only=True)
    component_type = serializers.CharField(read_only=True)
    
    class Meta:
        model = SubWorkOrder
        fields = [
            'id', 'parent_work_order', 'bom_component',
            'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status',
            'output_quantity', 'scrap_quantity',
            'target_category', 'notes', 'processes',
            'outputs', 'component_type', 'created_at',
            'modified_at'
        ]

class WorkOrderSerializer(serializers.ModelSerializer):
    sub_orders = SubWorkOrderSerializer(many=True, read_only=True)
    bom = BOMSerializer(read_only=True)
    
    class Meta:
        model = WorkOrder
        fields = [
            'id', 'order_number', 'sales_order_item', 'bom',
            'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status', 'priority',
            'notes', 'sub_orders', 'created_at', 'modified_at'
        ]

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = [
            'id', 'machine_code', 'machine_type', 'status',
            'brand', 'model', 'axis_count', 'internal_cooling',
            'motor_power_kva', 'holder_type', 'spindle_motor_power_10_percent_kw',
            'spindle_motor_power_30_percent_kw', 'power_hp', 'spindle_speed_rpm',
            'tool_count', 'nc_control_unit', 'manufacturing_year',
            'serial_number', 'machine_weight_kg', 'max_part_size',
            'description', 'maintenance_interval', 'last_maintenance_date',
            'next_maintenance_date', 'maintenance_notes', 'created_at', 'modified_at'
        ]

class WorkOrderOutputSerializer(serializers.ModelSerializer):
    target_category = InventoryCategorySerializer(read_only=True)
    
    class Meta:
        model = WorkOrderOutput
        fields = [
            'id', 'sub_work_order', 'quantity', 'status',
            'target_category', 'notes', 'quarantine_reason',
            'inspection_required', 'created_at', 'modified_at'
        ] 