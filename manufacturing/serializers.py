# manufacturing/serializers.py
from rest_framework import serializers
from .models import (
    ProductionLine, WorkCenter, WorkOrder, WorkOrderOperation,
    MaterialAllocation, ProductionOutput, MachineDowntime,
    ManufacturingProcess, ProductWorkflow, ProcessConfig,
    Fixture, ControlGauge, SubWorkOrder, Machine
)
from inventory.serializers import ProductSerializer
from core.serializers import UserListSerializer
from inventory.models import Product, ProductBOM
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


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
    production_line_name = serializers.StringRelatedField(source='production_line', read_only=True)
    
    class Meta:
        model = WorkCenter
        fields = [
            'id', 'code', 'name', 'description', 'production_line',
            'production_line_id', 'capacity_per_hour', 'setup_time_minutes',
            'is_active', 'created_at', 'production_line_name'
        ]
        read_only_fields = ['created_at']


class WorkOrderOperationSerializer(serializers.ModelSerializer):
    work_center = WorkCenterSerializer(read_only=True)
    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenter.objects.all(),
        source='work_center',
        write_only=True
    )
    work_center_name = serializers.StringRelatedField(source='work_center', read_only=True)
    assigned_to = UserListSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='assigned_to',
        write_only=True,
        required=False
    )
    assigned_to_name = serializers.StringRelatedField(source='assigned_to', read_only=True)
    
    class Meta:
        model = WorkOrderOperation
        fields = [
            'id', 'work_order', 'operation_sequence', 'operation_name',
            'work_center', 'work_center_id', 'work_center_name', 'planned_start_date',
            'planned_end_date', 'actual_start_date', 'actual_end_date',
            'setup_time_minutes', 'run_time_minutes', 'quantity_completed',
            'quantity_scrapped', 'status', 'assigned_to', 'assigned_to_id',
            'assigned_to_name', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']


class MaterialAllocationSerializer(serializers.ModelSerializer):
    material = ProductSerializer(read_only=True)
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='material',
        write_only=True
    )
    material_code = serializers.StringRelatedField(source='material.product_code', read_only=True)
    material_name = serializers.StringRelatedField(source='material.product_name', read_only=True)
    unit_of_measure = serializers.SerializerMethodField()
    
    class Meta:
        model = MaterialAllocation
        fields = [
            'id', 'work_order', 'material', 'material_id',
            'material_code', 'material_name', 'required_quantity',
            'allocated_quantity', 'consumed_quantity', 'is_allocated',
            'allocation_date', 'allocation_percentage', 'unit_of_measure'
        ]
        read_only_fields = ['allocation_percentage']
    
    def get_unit_of_measure(self, obj):
        return obj.material.unit_of_measure.unit_code if obj.material.unit_of_measure else None


class ProductionOutputSerializer(serializers.ModelSerializer):
    work_order = serializers.PrimaryKeyRelatedField(read_only=True)
    operation = serializers.PrimaryKeyRelatedField(read_only=True)
    operator = UserListSerializer(read_only=True)
    operator_name = serializers.StringRelatedField(source='operator', read_only=True)
    
    class Meta:
        model = ProductionOutput
        fields = [
            'id', 'work_order', 'operation', 'quantity_good',
            'quantity_scrapped', 'output_date', 'operator',
            'operator_name', 'batch_number', 'notes', 'created_at'
        ]
        read_only_fields = ['created_at']


class WorkOrderSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    product_code = serializers.StringRelatedField(source='product.product_code', read_only=True)
    product_name = serializers.StringRelatedField(source='product.product_name', read_only=True)
    work_center = WorkCenterSerializer(read_only=True)
    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenter.objects.all(),
        source='work_center',
        write_only=True
    )
    work_center_name = serializers.StringRelatedField(source='work_center', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    operations = WorkOrderOperationSerializer(many=True, read_only=True)
    material_allocations = MaterialAllocationSerializer(many=True, read_only=True)
    outputs = ProductionOutputSerializer(many=True, read_only=True)
    completion_percentage = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = WorkOrder
        fields = [
            'id', 'work_order_number', 'product', 'product_id',
            'product_code', 'product_name', 'quantity_ordered',
            'quantity_completed', 'quantity_scrapped', 'planned_start_date',
            'planned_end_date', 'actual_start_date', 'actual_end_date',
            'status', 'priority', 'work_center', 'work_center_id',
            'work_center_name', 'sales_order', 'notes', 'operations',
            'material_allocations', 'outputs', 'completion_percentage',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class MachineDowntimeSerializer(serializers.ModelSerializer):
    work_center = WorkCenterSerializer(read_only=True)
    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenter.objects.all(),
        source='work_center',
        write_only=True
    )
    work_center_name = serializers.StringRelatedField(source='work_center', read_only=True)
    reported_by = UserListSerializer(read_only=True)
    reported_by_name = serializers.StringRelatedField(source='reported_by', read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = MachineDowntime
        fields = [
            'id', 'work_center', 'work_center_id', 'work_center_name',
            'start_time', 'end_time', 'reason', 'category', 'notes',
            'reported_by', 'reported_by_name', 'duration_minutes', 'created_at'
        ]
        read_only_fields = ['created_at', 'reported_by']


# Serializers for new models
class ManufacturingProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturingProcess
        fields = '__all__'


class ProductWorkflowSerializer(serializers.ModelSerializer):
    product_code = serializers.StringRelatedField(source='product.product_code', read_only=True)
    product_name = serializers.StringRelatedField(source='product.product_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.StringRelatedField(source='approved_by', read_only=True)
    
    class Meta:
        model = ProductWorkflow
        fields = '__all__'


class ProcessConfigSerializer(serializers.ModelSerializer):
    process_name = serializers.StringRelatedField(source='process', read_only=True)
    workflow_version = serializers.StringRelatedField(source='workflow.version', read_only=True)
    product_code = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    axis_count_display = serializers.CharField(source='get_axis_count_display', read_only=True)
    
    class Meta:
        model = ProcessConfig
        fields = '__all__'
    
    def get_product_code(self, obj):
        return obj.workflow.product.product_code if obj.workflow and obj.workflow.product else None


class FixtureSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Fixture
        fields = '__all__'


class ControlGaugeSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ControlGauge
        fields = '__all__'


class SubWorkOrderSerializer(serializers.ModelSerializer):
    parent_order_number = serializers.StringRelatedField(source='parent_work_order.work_order_number', read_only=True)
    component_code = serializers.SerializerMethodField()
    target_category_name = serializers.StringRelatedField(source='target_category', read_only=True)
    assigned_to_name = serializers.StringRelatedField(source='assigned_to', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SubWorkOrder
        fields = '__all__'
    
    def get_component_code(self, obj):
        return obj.bom_component.component.product_code if obj.bom_component else None


class MachineSerializer(serializers.ModelSerializer):
    work_center_display = WorkCenterSerializer(source='work_center', read_only=True)
    is_maintenance_overdue = serializers.ReadOnlyField()
    machine_type_display = serializers.CharField(source='get_machine_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    axis_count_display = serializers.CharField(source='get_axis_count_display', read_only=True)
    
    class Meta:
        model = Machine
        fields = [
            'id', 'machine_code', 'machine_type', 'machine_type_display',
            'brand', 'model', 'axis_count', 'axis_count_display',
            'internal_cooling', 'motor_power_kva', 'holder_type',
            'spindle_motor_power_10_percent_kw', 'spindle_motor_power_30_percent_kw',
            'power_hp', 'spindle_speed_rpm', 'tool_count', 'nc_control_unit',
            'manufacturing_year', 'serial_number', 'machine_weight_kg',
            'max_part_size', 'description', 'status', 'status_display',
            'maintenance_interval', 'last_maintenance_date', 'next_maintenance_date',
            'maintenance_notes', 'work_center', 'work_center_display',
            'is_maintenance_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_serial_number(self, value):
        """Ensure serial number is unique if provided"""
        if value:
            machine_id = self.instance.id if self.instance else None
            if Machine.objects.filter(serial_number=value).exclude(id=machine_id).exists():
                raise serializers.ValidationError("A machine with this serial number already exists.")
        return value

    def validate(self, data):
        """Additional validation for machine data"""
        # Validate manufacturing year is not in the future
        if data.get('manufacturing_year'):
            from django.utils import timezone
            if data['manufacturing_year'] > timezone.now().date():
                raise serializers.ValidationError({
                    'manufacturing_year': 'Manufacturing year cannot be in the future.'
                })
        
        # Validate maintenance interval is positive
        if data.get('maintenance_interval', 0) <= 0:
            raise serializers.ValidationError({
                'maintenance_interval': 'Maintenance interval must be a positive number.'
            })
        
        return data


class MachineListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing machines"""
    work_center_name = serializers.CharField(source='work_center.name', read_only=True)
    is_maintenance_overdue = serializers.ReadOnlyField()
    machine_type_display = serializers.CharField(source='get_machine_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Machine
        fields = [
            'id', 'machine_code', 'machine_type', 'machine_type_display',
            'brand', 'model', 'status', 'status_display', 'work_center_name',
            'last_maintenance_date', 'next_maintenance_date',
            'is_maintenance_overdue', 'created_at'
        ]


class MachineDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for machine details with related data"""
    work_center_display = WorkCenterSerializer(source='work_center', read_only=True)
    downtime_history = serializers.SerializerMethodField()
    is_maintenance_overdue = serializers.ReadOnlyField()
    axis_count_display = serializers.CharField(source='get_axis_count_display', read_only=True)
    machine_type_display = serializers.CharField(source='get_machine_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Machine
        fields = [
            'id', 'machine_code', 'machine_type', 'machine_type_display',
            'brand', 'model', 'axis_count', 'axis_count_display',
            'internal_cooling', 'motor_power_kva', 'holder_type',
            'spindle_motor_power_10_percent_kw', 'spindle_motor_power_30_percent_kw',
            'power_hp', 'spindle_speed_rpm', 'tool_count', 'nc_control_unit',
            'manufacturing_year', 'serial_number', 'machine_weight_kg',
            'max_part_size', 'description', 'status', 'status_display',
            'maintenance_interval', 'last_maintenance_date', 'next_maintenance_date',
            'maintenance_notes', 'work_center', 'work_center_display',
            'is_maintenance_overdue', 'downtime_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_downtime_history(self, obj):
        """Get recent downtime history for this machine's work center"""
        if obj.work_center:
            downtime_records = MachineDowntime.objects.filter(
                work_center=obj.work_center
            ).order_by('-start_time')[:10]
            return MachineDowntimeSerializer(downtime_records, many=True).data
        return []