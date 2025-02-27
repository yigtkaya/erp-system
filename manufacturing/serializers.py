from rest_framework import serializers
from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput, BOMProcessConfig,
    ProcessComponent, ProductComponent, SubWorkOrderProcess,
    WorkOrderStatusChange
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
    active_bom_id = serializers.SerializerMethodField()

    class Meta:
        model = ProductComponent
        fields = [
            'id', 'bom', 'sequence_order', 'quantity',
            'notes', 'product', 'active_bom_id'
        ]
        extra_kwargs = {
            'quantity': {'required': True}
        }
    
    def get_active_bom_id(self, obj):
        """
        Return the ID of the active BOM for this product if it exists and is a SEMI product.
        This avoids redundant nesting of BOMs in the response.
        """
        if obj.product.product_type == 'SEMI':
            active_bom = BOM.objects.filter(
                product=obj.product,
                is_active=True
            ).order_by('-modified_at').first()
            
            if active_bom:
                return active_bom.id
        return None

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

    class Meta:
        model = SubWorkOrderProcess
        fields = [
            'id', 'sub_work_order', 'process', 'machine',
            'sequence_order', 'planned_duration_minutes',
            'actual_duration_minutes', 'status', 'status_display',
            'start_time', 'end_time', 'operator',
            'setup_time_minutes', 'notes'
        ]

class SubWorkOrderProcessCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubWorkOrderProcess
        fields = [
            'id', 'sub_work_order', 'process', 'machine',
            'sequence_order', 'planned_duration_minutes',
            'actual_duration_minutes', 'status',
            'start_time', 'end_time', 'operator',
            'setup_time_minutes', 'notes'
        ]

    def validate(self, data):
        # Validate machine compatibility with process
        if 'machine' in data and 'process' in data:
            machine = data['machine']
            process = data['process']
            
            if machine.machine_type != process.machine_type:
                raise serializers.ValidationError("Machine type does not match process requirements")
                
            if machine.status != 'AVAILABLE':
                raise serializers.ValidationError("Selected machine is not available")
        
        # Validate time tracking
        if 'start_time' in data and 'end_time' in data:
            if data['end_time'] and data['start_time'] and data['end_time'] < data['start_time']:
                raise serializers.ValidationError("End time cannot be before start time")
        
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