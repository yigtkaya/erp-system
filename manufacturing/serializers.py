from rest_framework import serializers
from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput,
    SubWorkOrderProcess, WorkOrderStatusChange, WorkflowProcess,
    ProcessConfig
)
from inventory.serializers import InventoryCategorySerializer, ProductSerializer, RawMaterialSerializer
from django.db import transaction
from erp_core.serializers import UserSerializer

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

class ManufacturingProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturingProcess
        fields = [
            'id', 'process_code', 'process_name',
            'created_at', 'modified_at'
        ]

class WorkflowProcessSerializer(serializers.ModelSerializer):
    process_details = ManufacturingProcessSerializer(source='process', read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)
    process_configs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = WorkflowProcess
        fields = [
            'id', 'product', 'product_details',
            'process', 'process_details',
            'stock_code', 'sequence_order',
            'process_configs', 'created_at', 'modified_at'
        ]

class WorkflowProcessCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowProcess
        fields = [
            'product', 'process',
            'stock_code', 'sequence_order'
        ]

    def validate(self, data):
        # Check for duplicate sequence_order within the same product
        if 'product' in data and 'sequence_order' in data:
            product = data['product']
            sequence_order = data['sequence_order']
            
            # If updating an existing instance, exclude the current instance from the check
            instance_id = self.instance.id if self.instance else None
            
            # Check if another process with the same sequence_order exists for this product
            exists = WorkflowProcess.objects.filter(
                product=product,
                sequence_order=sequence_order
            )
            
            if instance_id:
                exists = exists.exclude(id=instance_id)
                
            if exists.exists():
                raise serializers.ValidationError({
                    'sequence_order': f'A process with sequence order {sequence_order} already exists for this product.'
                })

        # Check for duplicate product-process-stock_code combination
        if all(key in data for key in ['product', 'process', 'stock_code']):
            product = data['product']
            process = data['process']
            stock_code = data['stock_code']
            
            exists = WorkflowProcess.objects.filter(
                product=product,
                process=process,
                stock_code=stock_code
            )
            
            if instance_id:
                exists = exists.exclude(id=instance_id)
                
            if exists.exists():
                raise serializers.ValidationError({
                    'non_field_errors': 'A workflow process with this product, process, and stock code combination already exists.'
                })
                
        return data

class ProcessConfigSerializer(serializers.ModelSerializer):
    workflow_process_details = WorkflowProcessSerializer(source='workflow_process', read_only=True)
    cycle_time = serializers.FloatField(source='get_cycle_time', read_only=True)
    tool_details = serializers.SerializerMethodField()
    control_gauge_details = serializers.SerializerMethodField()
    fixture_details = serializers.SerializerMethodField()

    class Meta:
        model = ProcessConfig
        fields = [
            'id', 'workflow_process', 'workflow_process_details',
            'tool', 'tool_details',
            'control_gauge', 'control_gauge_details',
            'fixture', 'fixture_details',
            'axis_count', 'machine_time', 'setup_time', 'net_time',
            'number_of_bindings', 'cycle_time',
            'created_at', 'modified_at'
        ]

    def get_tool_details(self, obj):
        if obj.tool:
            return {
                'stock_code': obj.tool.stock_code,
                'name': obj.tool.tool_type,
                'material': obj.tool.tool_material,
                'diameter': obj.tool.tool_diameter,
                'length': obj.tool.tool_length,
                'width': obj.tool.tool_width,
                'height': obj.tool.tool_height,
                'angle': obj.tool.tool_angle,
                'radius': obj.tool.tool_radius,
                'connection_diameter': obj.tool.tool_connection_diameter,
                'status': obj.tool.status
            }
        return None

    def get_control_gauge_details(self, obj):
        if obj.control_gauge:
            return {
                'stock_code': obj.control_gauge.stock_code,
                'name': obj.control_gauge.stock_name,
                'type': obj.control_gauge.stock_type,
                'description': obj.control_gauge.description
            }
        return None

    def get_fixture_details(self, obj):
        if obj.fixture:
            return {
                'code': obj.fixture.code,
                'name': obj.fixture.name,
                'status': obj.fixture.status
            }
        return None

class ProcessConfigCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessConfig
        fields = [
            'workflow_process', 'tool', 'control_gauge',
            'fixture', 'axis_count', 'machine_time',
            'setup_time', 'net_time', 'number_of_bindings'
        ]

    def validate(self, data):
        # Validate time fields are non-negative
        for field in ['machine_time', 'setup_time', 'net_time']:
            value = data.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({
                    field: f'{field.replace("_", " ").title()} cannot be negative'
                })

        # Validate number of bindings
        bindings = data.get('number_of_bindings')
        if bindings is not None and bindings < 0:
            raise serializers.ValidationError({
                'number_of_bindings': 'Number of bindings cannot be negative'
            })

        return data

class BOMComponentSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source='product.product_code', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    product_type = serializers.CharField(source='product.product_type', read_only=True)

    class Meta:
        model = BOMComponent
        fields = [
            'id', 'bom', 'sequence_order', 'quantity', 
            'product', 'product_code', 'product_name', 'product_type',
            'lead_time_days', 'notes'
        ]
        read_only_fields = ['id']

class BOMComponentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMComponent
        fields = [
            'bom', 'sequence_order', 'quantity',
            'product', 'lead_time_days', 'notes'
        ]

    def validate(self, data):
        # Validate sequence order is unique within BOM
        if self.instance:  # For updates
            exists = BOMComponent.objects.filter(
                bom=data.get('bom', self.instance.bom),
                sequence_order=data.get('sequence_order', self.instance.sequence_order)
            ).exclude(pk=self.instance.pk).exists()
        else:  # For creates
            exists = BOMComponent.objects.filter(
                bom=data['bom'],
                sequence_order=data['sequence_order']
            ).exists()
            
        if exists:
            raise serializers.ValidationError(
                {'sequence_order': 'A component with this sequence order already exists in this BOM.'}
            )
            
        return data

class BOMSerializer(serializers.ModelSerializer):
    components = BOMComponentSerializer(many=True, read_only=True)
    product = ProductSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = BOM
        fields = [
            'id', 'product', 'version', 'is_active', 'is_approved',
            'approved_by', 'approved_at', 'parent_bom', 'notes',
            'components', 'created_at', 'modified_at'
        ]

class BOMCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOM
        fields = [
            'id', 'product', 'version', 'is_active', 'notes'
        ]
    
    def validate(self, data):
        print("\n=== BOM Serializer Validation Debug ===")
        print("1. Incoming data:", data)
        print("2. Data type:", type(data))
        
        if 'product' in data:
            try:
                from inventory.models import Product
                product_code = data['product']
                print("3. Looking for product with code:", product_code)
                print("4. Product code type:", type(product_code))
                
                # If product is already a Product instance, use it directly
                if isinstance(product_code, Product):
                    product = product_code
                else:
                    # Otherwise, look up by product_code
                    product = Product.objects.get(product_code=product_code)
                
                print("5. Found product:", product.product_code)
                print("6. Product type:", product.product_type)
                
                if product.product_type == 'STANDARD_PART':
                    print("7. Error: Product is a STANDARD_PART")
                    raise serializers.ValidationError({
                        "product": "Standard products (bought externally) cannot have a BOM"
                    })
                
                # Check for existing BOM with same product and version
                if 'version' in data:
                    print("8. Checking for existing BOM with version:", data['version'])
                    existing_bom = BOM.objects.filter(
                        product=product,
                        version=data['version']
                    )
                    if self.instance:
                        existing_bom = existing_bom.exclude(pk=self.instance.pk)
                    
                    if existing_bom.exists():
                        print("9. Error: BOM already exists with this version")
                        print("10. Existing BOM:", existing_bom.first())
                        print("11. Is active:", existing_bom.first().is_active)
                        raise serializers.ValidationError({
                            "version": f"BOM with version {data['version']} already exists for this product"
                        })
                    print("9. No existing BOM found with this version")
                
                # Replace the product code with the actual product instance
                data['product'] = product
                print("10. Validation successful, returning data:", data)
                
            except Product.DoesNotExist:
                error_msg = f"Product with code {product_code} does not exist"
                print("Error:", error_msg)
                raise serializers.ValidationError({
                    "product": error_msg
                })
            except Exception as e:
                print("Unexpected error during validation:")
                print("Type:", type(e))
                print("Details:", str(e))
                raise
        return data

class BOMWithComponentsSerializer(serializers.ModelSerializer):
    components = BOMComponentCreateUpdateSerializer(many=True, required=False)
    
    class Meta:
        model = BOM
        fields = [
            'id', 'product', 'version', 'is_active', 'notes'
        ]
    
    def validate(self, data):
        if 'product' in data:
            product = data['product']
            if product.product_type == 'STANDARD_PART':
                raise serializers.ValidationError("Standard products (bought externally) cannot have a BOM")
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        components_data = validated_data.pop('components', [])
        bom = BOM.objects.create(**validated_data)
        
        for component_data in components_data:
            component_data['bom'] = bom
            component_serializer = BOMComponentCreateUpdateSerializer(data=component_data)
            component_serializer.is_valid(raise_exception=True)
            component_serializer.save()
        
        return bom

class WorkOrderStatusChangeSerializer(serializers.ModelSerializer):
    changed_by = UserSerializer(read_only=True)
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    
    class Meta:
        model = WorkOrderStatusChange
        fields = [
            'id', 'work_order', 'from_status', 'to_status',
            'from_status_display', 'to_status_display',
            'changed_by', 'changed_at', 'notes'
        ]

class SubWorkOrderProcessSerializer(serializers.ModelSerializer):
    process = ManufacturingProcessSerializer(read_only=True)
    machine = MachineSerializer(read_only=True)
    operator = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    workflow_process_details = WorkflowProcessSerializer(source='workflow_process', read_only=True)
    process_config_details = ProcessConfigSerializer(source='process_config', read_only=True)

    class Meta:
        model = SubWorkOrderProcess
        fields = [
            'id', 'sub_work_order', 'workflow_process', 'workflow_process_details',
            'process_config', 'process_config_details',
            'machine', 'sequence_order', 'planned_duration_minutes',
            'actual_duration_minutes', 'status', 'status_display',
            'start_time', 'end_time', 'operator', 'setup_time_minutes',
            'notes'
        ]

class SubWorkOrderProcessCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubWorkOrderProcess
        fields = [
            'sub_work_order', 'workflow_process', 'process_config',
            'machine', 'sequence_order', 'planned_duration_minutes',
            'status', 'start_time', 'end_time', 'operator',
            'setup_time_minutes', 'notes'
        ]

    def validate(self, data):
        # Ensure process_config belongs to the workflow_process if both are provided
        workflow_process = data.get('workflow_process')
        process_config = data.get('process_config')
                
        if workflow_process and process_config and process_config.workflow_process != workflow_process:
            raise serializers.ValidationError(
                "The selected process configuration does not belong to the selected workflow process"
            )
                
        return data

class SubWorkOrderSerializer(serializers.ModelSerializer):
    processes = SubWorkOrderProcessSerializer(many=True, read_only=True)
    outputs = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    target_category = InventoryCategorySerializer(read_only=True)
    component_type = serializers.CharField(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SubWorkOrder
        fields = [
            'id', 'parent_work_order', 'bom_component',
            'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status', 'status_display',
            'output_quantity', 'scrap_quantity',
            'target_category', 'notes', 'processes',
            'outputs', 'component_type', 'completion_percentage',
            'assigned_to'
        ]

class SubWorkOrderCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubWorkOrder
        fields = [
            'id', 'parent_work_order', 'bom_component',
            'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status',
            'output_quantity', 'scrap_quantity',
            'target_category', 'notes', 'completion_percentage',
            'assigned_to'
        ]

    def validate(self, data):
        # Validate dates
        if 'planned_start' in data and 'planned_end' in data:
            if data['planned_end'] < data['planned_start']:
                raise serializers.ValidationError("Planned end date cannot be before planned start date")
        
        # Validate quantities
        if 'output_quantity' in data and 'scrap_quantity' in data and 'quantity' in data:
            if data['output_quantity'] and data['output_quantity'] + data.get('scrap_quantity', 0) > data['quantity']:
                raise serializers.ValidationError("Output quantity plus scrap cannot exceed input quantity")
        
        # Validate status transitions
        if 'status' in data and self.instance:
            from .models import WorkOrderStatusTransition
            if not WorkOrderStatusTransition.is_valid_transition(self.instance.status, data['status']):
                raise serializers.ValidationError(f"Invalid status transition from {self.instance.status} to {data['status']}")
        
        return data

class WorkOrderSerializer(serializers.ModelSerializer):
    sub_orders = SubWorkOrderSerializer(many=True, read_only=True)
    bom = BOMSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'order_number', 'sales_order_item',
            'bom', 'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status', 'status_display',
            'priority', 'notes', 'sub_orders', 'completion_percentage',
            'assigned_to'
        ]

class WorkOrderCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = [
            'id', 'order_number', 'sales_order_item',
            'bom', 'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status',
            'priority', 'notes', 'completion_percentage',
            'assigned_to'
        ]

    def validate(self, data):
        # Validate dates
        if 'planned_start' in data and 'planned_end' in data:
            if data['planned_end'] < data['planned_start']:
                raise serializers.ValidationError("Planned end date cannot be before planned start date")
        
        # Validate BOM is approved
        if 'bom' in data and not data['bom'].is_approved:
            raise serializers.ValidationError("Cannot create work order with unapproved BOM")
        
        # Validate status transitions
        if 'status' in data and self.instance:
            from .models import WorkOrderStatusTransition
            if not WorkOrderStatusTransition.is_valid_transition(self.instance.status, data['status']):
                raise serializers.ValidationError(f"Invalid status transition from {self.instance.status} to {data['status']}")
        
        return data

class WorkOrderOutputSerializer(serializers.ModelSerializer):
    target_category = InventoryCategorySerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WorkOrderOutput
        fields = [
            'id', 'sub_work_order', 'quantity', 'status',
            'status_display', 'target_category', 'notes',
            'quarantine_reason', 'inspection_required',
            'created_by', 'production_date', 'created_at'
        ]

class WorkOrderOutputCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderOutput
        fields = [
            'id', 'sub_work_order', 'quantity', 'status',
            'target_category', 'notes', 'quarantine_reason',
            'inspection_required', 'production_date'
        ]

    def validate(self, data):
        # Validate quantity
        if 'quantity' in data and data['quantity'] <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
            
        # Validate quarantine reason
        if 'status' in data and data['status'] == 'QUARANTINE' and not data.get('quarantine_reason'):
            raise serializers.ValidationError("Quarantine reason is required for items in quarantine status")
            
        # Validate target category based on status
        if 'status' in data and 'target_category' in data:
            status = data['status']
            target_category = data['target_category']
            
            if status == 'GOOD':
                # Target category validation will be handled in the model's clean method
                pass
            elif status == 'REWORK' and target_category.name != 'KARANTINA':
                raise serializers.ValidationError("Items needing rework must go to Karantina")
            elif status == 'SCRAP' and target_category.name != 'HURDA':
                raise serializers.ValidationError("Scrap items must go to Hurda")
            elif status == 'QUARANTINE' and target_category.name != 'KARANTINA':
                raise serializers.ValidationError("Quarantined items must go to Karantina category")
                
        # Validate total output doesn't exceed work order quantity
        if 'sub_work_order' in data and 'quantity' in data:
            sub_work_order = data['sub_work_order']
            quantity = data['quantity']
            
            # Get existing outputs for this sub work order
            existing_quantity = 0
            if self.instance:
                existing_quantity = WorkOrderOutput.objects.filter(
                    sub_work_order=sub_work_order
                ).exclude(pk=self.instance.pk).aggregate(
                    total=models.Sum('quantity')
                )['total'] or 0
            else:
                existing_quantity = WorkOrderOutput.objects.filter(
                    sub_work_order=sub_work_order
                ).aggregate(total=models.Sum('quantity'))['total'] or 0
                
            if existing_quantity + quantity > sub_work_order.quantity:
                raise serializers.ValidationError(
                    f"Total output quantity ({existing_quantity + quantity}) cannot exceed work order quantity ({sub_work_order.quantity})"
                )
                
        return data