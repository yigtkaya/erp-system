from rest_framework import serializers
from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput, BOMProcessConfig,
    ProcessComponent, ProductComponent, SubWorkOrderProcess
)
from inventory.serializers import InventoryCategorySerializer, ProductSerializer, RawMaterialSerializer
from django.db import transaction

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

class ProcessComponentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessComponent
        fields = [
            'id', 'bom', 'sequence_order', 'quantity',
            'notes', 'process_config', 'raw_material'
        ]
        extra_kwargs = {
            'quantity': {'required': False}
        }

    def validate(self, data):
        # Validate that the BOM product is of type SEMI or SINGLE
        if 'bom' in data:
            bom = data['bom']
            if bom.product.product_type not in ['SEMI', 'SINGLE']:
                raise serializers.ValidationError("Process components can only be added to BOMs for Semi or Single products")
        return data

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

class ProductComponentCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductComponent
        fields = [
            'id', 'bom', 'sequence_order', 'quantity',
            'notes', 'product'
        ]
        extra_kwargs = {
            'quantity': {'required': True}
        }

    def validate(self, data):
        if 'bom' in data and 'product' in data:
            bom = data['bom']
            product = data['product']
            
            # Check for self-reference
            if bom.product == product:
                raise serializers.ValidationError("A product cannot be a component of itself")
            
            # Validate based on parent product type
            parent_type = bom.product.product_type
            if parent_type == 'MONTAGED':
                if product.product_type not in ['SEMI', 'STANDARD_PART']:
                    raise serializers.ValidationError("Montaged products can only contain Semi or Standard products as components")
            elif parent_type in ['SEMI', 'SINGLE']:
                if product.product_type != 'STANDARD_PART':
                    raise serializers.ValidationError("Semi and Single products can only include Standard parts as product components")
        
        if 'quantity' not in data or data['quantity'] is None:
            raise serializers.ValidationError({"quantity": "Quantity is required for product components"})
            
        return data

class BOMComponentSerializer(serializers.ModelSerializer):
    process_component = ProcessComponentSerializer(source='processcomponent', read_only=True)
    product_component = ProductComponentSerializer(source='productcomponent', read_only=True)
    component_type = serializers.CharField(source='get_component_type_display', read_only=True)

    class Meta:
        model = BOMComponent
        fields = [
            'id', 'bom', 'sequence_order', 'quantity',
            'notes', 'component_type', 'process_component', 
            'product_component'
        ]

class BOMComponentCreateSerializer(serializers.Serializer):
    bom = serializers.PrimaryKeyRelatedField(queryset=BOM.objects.all())
    sequence_order = serializers.IntegerField(min_value=1)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    component_type = serializers.ChoiceField(choices=['PRODUCT', 'PROCESS'])
    
    # Fields for product component
    product = serializers.IntegerField(required=False, help_text="Product ID when component_type is PRODUCT")
    
    # Fields for process component
    process_config = serializers.PrimaryKeyRelatedField(
        queryset=BOMProcessConfig.objects.all(), required=False,
        help_text="Required when component_type is PROCESS"
    )
    raw_material = serializers.IntegerField(required=False, allow_null=True, help_text="RawMaterial ID (optional for process components)")
    
    def validate(self, data):
        component_type = data.get('component_type')
        
        # Validate required fields based on component type
        if component_type == 'PRODUCT':
            if 'product' not in data:
                raise serializers.ValidationError({"product": "Product is required for product components"})
            if 'quantity' not in data or data['quantity'] is None:
                raise serializers.ValidationError({"quantity": "Quantity is required for product components"})
            
            # Validate product exists
            from inventory.models import Product
            try:
                product = Product.objects.get(pk=data['product'])
                data['product'] = product  # Replace ID with actual object
            except Product.DoesNotExist:
                raise serializers.ValidationError({"product": "Product does not exist"})
                
        elif component_type == 'PROCESS':
            if 'process_config' not in data:
                raise serializers.ValidationError({"process_config": "Process configuration is required for process components"})
            
            # Validate raw_material exists if provided
            if 'raw_material' in data and data['raw_material'] is not None:
                from inventory.models import RawMaterial
                try:
                    raw_material = RawMaterial.objects.get(pk=data['raw_material'])
                    data['raw_material'] = raw_material  # Replace ID with actual object
                except RawMaterial.DoesNotExist:
                    raise serializers.ValidationError({"raw_material": "Raw material does not exist"})
        
        # Check for duplicate sequence_order
        bom = data.get('bom')
        sequence_order = data.get('sequence_order')
        if bom and sequence_order:
            if BOMComponent.objects.filter(bom=bom, sequence_order=sequence_order).exists():
                raise serializers.ValidationError(
                    {"sequence_order": f"A component with sequence order {sequence_order} already exists in this BOM"}
                )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        component_type = validated_data.pop('component_type')
        
        if component_type == 'PRODUCT':
            product = validated_data.pop('product')
            # Remove process component fields if present
            validated_data.pop('process_config', None)
            validated_data.pop('raw_material', None)
            
            return ProductComponent.objects.create(
                product=product,
                **validated_data
            )
        else:  # PROCESS
            process_config = validated_data.pop('process_config')
            raw_material = validated_data.pop('raw_material', None)
            # Remove product component fields if present
            validated_data.pop('product', None)
            
            return ProcessComponent.objects.create(
                process_config=process_config,
                raw_material=raw_material,
                **validated_data
            )

class BOMSerializer(serializers.ModelSerializer):
    components = BOMComponentSerializer(many=True, read_only=True)
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = BOM
        fields = [
            'id', 'product', 'version', 'is_active',
            'components', 'created_at', 'modified_at'
        ]

class BOMCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOM
        fields = [
            'id', 'product', 'version', 'is_active'
        ]
    
    def validate(self, data):
        if 'product' in data:
            product = data['product']
            if product.product_type == 'STANDARD_PART':
                raise serializers.ValidationError("Standard products (bought externally) cannot have a BOM")
        return data

class BOMWithComponentsSerializer(serializers.ModelSerializer):
    components = BOMComponentCreateSerializer(many=True, required=False)
    
    class Meta:
        model = BOM
        fields = [
            'id', 'product', 'version', 'is_active',
            'components', 'created_at', 'modified_at'
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
            component_serializer = BOMComponentCreateSerializer(data=component_data)
            component_serializer.is_valid(raise_exception=True)
            component_serializer.save()
        
        return bom

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

class SubWorkOrderProcessCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubWorkOrderProcess
        fields = [
            'id', 'sub_work_order', 'process', 'machine',
            'sequence_order', 'planned_duration_minutes',
            'actual_duration_minutes'
        ]
    
    def validate(self, data):
        if 'sub_work_order' in data and 'process' in data and 'machine' in data:
            sub_work_order = data['sub_work_order']
            process = data['process']
            machine = data['machine']
            
            # Ensure the sub work order is for a process component
            if not sub_work_order.is_process_component:
                raise serializers.ValidationError("Can only add processes to sub work orders with process components")
            
            process_component = sub_work_order.get_specific_component()
            
            # Validate machine requirements against the process configuration
            if process_component.process_config.axis_count and machine.axis_count != process_component.process_config.axis_count:
                raise serializers.ValidationError("Machine axis count does not match process requirements")
            
            if machine.machine_type != process_component.process_config.process.machine_type:
                raise serializers.ValidationError("Machine type does not match process requirements")
            
            if process != process_component.process_config.process:
                raise serializers.ValidationError("Process must match the one specified in the BOM process configuration")
        
        return data

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

class SubWorkOrderCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubWorkOrder
        fields = [
            'id', 'parent_work_order', 'bom_component',
            'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status',
            'output_quantity', 'scrap_quantity',
            'target_category', 'notes'
        ]
    
    def validate(self, data):
        if 'output_quantity' in data and 'scrap_quantity' in data and 'quantity' in data:
            output_quantity = data['output_quantity']
            scrap_quantity = data['scrap_quantity']
            quantity = data['quantity']
            
            if output_quantity and output_quantity + scrap_quantity > quantity:
                raise serializers.ValidationError("Output quantity plus scrap cannot exceed input quantity")
        
        if 'status' in data and data['status'] == 'COMPLETED' and ('output_quantity' not in data or not data['output_quantity']):
            raise serializers.ValidationError("Output quantity must be set when completing a work order")
        
        return data

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

class WorkOrderCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrder
        fields = [
            'id', 'order_number', 'sales_order_item', 'bom',
            'quantity', 'planned_start', 'planned_end',
            'actual_start', 'actual_end', 'status', 'priority',
            'notes'
        ]
    
    def validate(self, data):
        if 'planned_start' in data and 'planned_end' in data:
            if data['planned_start'] > data['planned_end']:
                raise serializers.ValidationError("Planned end date must be after planned start date")
        
        if 'actual_start' in data and 'actual_end' in data:
            if data['actual_start'] and data['actual_end'] and data['actual_start'] > data['actual_end']:
                raise serializers.ValidationError("Actual end date must be after actual start date")
        
        return data

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

class WorkOrderOutputCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOrderOutput
        fields = [
            'id', 'sub_work_order', 'quantity', 'status',
            'target_category', 'notes', 'quarantine_reason',
            'inspection_required'
        ]
    
    def validate(self, data):
        if 'status' in data and data['status'] == 'QUARANTINE' and 'quarantine_reason' not in data:
            raise serializers.ValidationError({"quarantine_reason": "Quarantine reason is required for items in quarantine status"})
        
        if 'sub_work_order' in data and 'quantity' in data:
            sub_work_order = data['sub_work_order']
            quantity = data['quantity']
            
            # Calculate total output excluding this instance
            instance_id = self.instance.id if self.instance else None
            total_output = WorkOrderOutput.objects.filter(sub_work_order=sub_work_order).exclude(pk=instance_id).aggregate(
                total=serializers.Sum('quantity'))['total'] or 0
            
            if total_output + quantity > sub_work_order.quantity:
                raise serializers.ValidationError("Total output quantity cannot exceed work order quantity")
        
        return data