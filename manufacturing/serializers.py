from rest_framework import serializers
from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput,
    SubWorkOrderProcess, WorkOrderStatusChange, WorkflowProcess
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

class WorkflowProcessSerializer(serializers.ModelSerializer):
    process_details = ManufacturingProcessSerializer(source='process', read_only=True)
    raw_material_details = RawMaterialSerializer(source='raw_material', read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = WorkflowProcess
        fields = [
            'id', 'product', 'product_details',
            'process', 'process_details',
            'process_number', 'stock_code',
            'raw_material', 'raw_material_details',
            'requires_machine', 'axis_count',
            'estimated_duration_minutes',
            'tooling_requirements', 'quality_checks',
            'sequence_order', 'created_at', 'modified_at'
        ]

class WorkflowProcessCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowProcess
        fields = [
            'id', 'product', 'process',
            'process_number', 'stock_code',
            'raw_material', 'requires_machine',
            'axis_count', 'estimated_duration_minutes',
            'tooling_requirements', 'quality_checks',
            'sequence_order'
        ]

    def validate(self, data):
        # Validate axis_count based on requires_machine
        requires_machine = data.get('requires_machine', False)
        axis_count = data.get('axis_count')
        
        if requires_machine and not axis_count:
            raise serializers.ValidationError(
                "Axis count is required when process requires a machine"
            )
        if not requires_machine and axis_count:
            raise serializers.ValidationError(
                "Axis count should not be set for processes that don't require machines"
            )

        # Validate sequence_order uniqueness
        product = data.get('product')
        sequence_order = data.get('sequence_order')
        
        if product and sequence_order:
            exists = WorkflowProcess.objects.filter(
                product=product,
                sequence_order=sequence_order
            )
            if self.instance:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise serializers.ValidationError(
                    "A process with this sequence order already exists for this product"
                )
        
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