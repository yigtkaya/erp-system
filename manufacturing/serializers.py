# manufacturing/serializers.py
from rest_framework import serializers
from .models import (
 WorkOrder, WorkOrderOperation,
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

class MachineSerializer(serializers.ModelSerializer):
    is_maintenance_overdue = serializers.ReadOnlyField()
    machine_type_display = serializers.CharField(source='get_machine_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    axis_count_display = serializers.CharField(source='get_axis_count_display', read_only=True)

    class Meta:
        model = Machine
        fields = [
            'id', 'machine_code', 'machine_type', 'machine_type_display',
            'brand', 'model',
            'axis_count', 'axis_count_display', 'internal_cooling', 'motor_power_kva',
            'holder_type', 'spindle_motor_power_10_percent_kw', 'spindle_motor_power_30_percent_kw',
            'power_hp', 'spindle_speed_rpm', 'tool_count', 'nc_control_unit',
            'manufacturing_year', 'serial_number', 'machine_weight_kg',
            'max_part_size', 'description', 'status', 'status_display',
            'maintenance_interval', 'last_maintenance_date', 'next_maintenance_date',
            'maintenance_notes', 'is_active', 'is_maintenance_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_serial_number(self, value):
        if value and Machine.objects.filter(serial_number=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Serial number must be unique.")
        return value

    def validate(self, data):
        # Validate machine specifications based on machine type
        machine_type = data.get('machine_type')
        
        if machine_type in ['CNC_MILLING', 'CNC_LATHE']:
            required_fields = ['axis_count', 'spindle_speed_rpm', 'tool_count']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(f"{field} is required for {machine_type}")
        
        return data


class WorkOrderOperationSerializer(serializers.ModelSerializer):
    machine = MachineSerializer(read_only=True)
    machine_id = serializers.PrimaryKeyRelatedField(
        queryset=Machine.objects.all(),
        source='machine',
        write_only=True
    )
    machine_code = serializers.StringRelatedField(source='machine.machine_code', read_only=True)
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
            'machine', 'machine_id', 'machine_code', 'planned_start_date',
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
    primary_machine = MachineSerializer(read_only=True)
    primary_machine_id = serializers.PrimaryKeyRelatedField(
        queryset=Machine.objects.all(),
        source='primary_machine',
        write_only=True,
        required=False
    )
    primary_machine_code = serializers.StringRelatedField(source='primary_machine.machine_code', read_only=True)
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
            'status', 'priority', 'primary_machine', 'primary_machine_id',
            'primary_machine_code', 'sales_order', 'notes', 'operations',
            'material_allocations', 'outputs', 'completion_percentage',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class MachineDowntimeSerializer(serializers.ModelSerializer):
    machine = MachineSerializer(read_only=True)
    machine_id = serializers.PrimaryKeyRelatedField(
        queryset=Machine.objects.all(),
        source='machine',
        write_only=True
    )
    machine_code = serializers.StringRelatedField(source='machine.machine_code', read_only=True)
    reported_by = UserListSerializer(read_only=True)
    reported_by_name = serializers.StringRelatedField(source='reported_by', read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    
    class Meta:
        model = MachineDowntime
        fields = [
            'id', 'machine', 'machine_id', 'machine_code',
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
    machine_type_display = serializers.CharField(source='get_machine_type_display', read_only=True)
    
    class Meta:
        model = ProcessConfig
        fields = [
            'id', 'workflow', 'process', 'sequence_order', 'version', 'status',
            'machine_type', 'axis_count', 'tool', 'fixture', 'control_gauge',
            'setup_time', 'cycle_time', 'connecting_count', 'quality_requirements',
            'instructions', 'process_name', 'workflow_version', 'product_code',
            'status_display', 'axis_count_display', 'machine_type_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'sequence_order']
    
    def get_product_code(self, obj):
        return obj.workflow.product.product_code if obj.workflow and obj.workflow.product else None
    
    def validate(self, data):
        """Validate ProcessConfig data"""
        # Validate time parameters are non-negative
        time_fields = ['setup_time', 'cycle_time', 'connecting_count']
        for field in time_fields:
            if field in data and data[field] < 0:
                raise serializers.ValidationError(f"{field} must be non-negative")
        
        # Validate machine type and axis count compatibility
        machine_type = data.get('machine_type')
        axis_count = data.get('axis_count')
        
        if machine_type and axis_count:
            if machine_type in ['CNC_MILLING', 'CNC_LATHE'] and axis_count == 'MULTI':
                raise serializers.ValidationError("CNC machines should have specific axis count, not MULTI")
            elif machine_type in ['ASSEMBLY', 'INSPECTION'] and axis_count not in [None, '']:
                raise serializers.ValidationError(f"{machine_type} machines typically don't require axis count specification")
        
        return data


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
        return obj.bom_component.child_product.product_code if obj.bom_component else None


class MachineListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing machines"""
    is_maintenance_overdue = serializers.ReadOnlyField()
    machine_type_display = serializers.CharField(source='get_machine_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Machine
        fields = [
            'id', 'machine_code', 'machine_type', 'machine_type_display',
            'brand', 'model', 'status', 'status_display',
            'is_maintenance_overdue'
        ]


class MachineDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for machine details with related data"""
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
            'maintenance_notes',
            'is_maintenance_overdue', 'downtime_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_downtime_history(self, obj):
        """Get recent downtime history for this machine"""
        from .models import MachineDowntime
        downtimes = MachineDowntime.objects.filter(machine=obj).order_by('-start_time')[:5]
        return MachineDowntimeSerializer(downtimes, many=True).data


class ProductBOMSerializer(serializers.ModelSerializer):
    """Serializer for ProductBOM (Bill of Materials)"""
    parent_product = ProductSerializer(read_only=True)
    parent_product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='parent_product',
        write_only=True
    )
    child_product = ProductSerializer(read_only=True)
    child_product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='child_product',
        write_only=True
    )
    parent_product_code = serializers.StringRelatedField(source='parent_product.stock_code', read_only=True)
    parent_product_name = serializers.StringRelatedField(source='parent_product.product_name', read_only=True)
    child_product_code = serializers.StringRelatedField(source='child_product.stock_code', read_only=True)
    child_product_name = serializers.StringRelatedField(source='child_product.product_name', read_only=True)
    child_product_type = serializers.StringRelatedField(source='child_product.product_type', read_only=True)
    unit_of_measure = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductBOM
        fields = [
            'id', 'parent_product', 'parent_product_id', 'parent_product_code', 'parent_product_name',
            'child_product', 'child_product_id', 'child_product_code', 'child_product_name', 'child_product_type',
            'quantity', 'scrap_percentage', 'operation_sequence', 'notes', 'unit_of_measure',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_unit_of_measure(self, obj):
        return obj.child_product.unit_of_measure.unit_code if obj.child_product.unit_of_measure else None
    
    def validate(self, data):
        """Validate BOM data"""
        parent_product = data.get('parent_product')
        child_product = data.get('child_product')
        
        if parent_product and child_product:
            if parent_product == child_product:
                raise serializers.ValidationError("A product cannot be a component of itself")
            
            # Check for existing BOM item
            if ProductBOM.objects.filter(
                parent_product=parent_product,
                child_product=child_product
            ).exclude(id=self.instance.id if self.instance else None).exists():
                raise serializers.ValidationError("This BOM item already exists")
        
        return data