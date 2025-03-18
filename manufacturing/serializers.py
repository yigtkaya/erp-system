from rest_framework import serializers
from .models import (
    WorkOrder, BOM, Machine, ManufacturingProcess,
    SubWorkOrder, BOMComponent, WorkOrderOutput,
    SubWorkOrderProcess, WorkOrderStatusChange,
    ProcessConfig, ProductWorkflow
)
from inventory.serializers import InventoryCategorySerializer, ProductSerializer, RawMaterialSerializer
from django.db import transaction
from erp_core.serializers import UserSerializer

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = '__all__'

class ManufacturingProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturingProcess
        fields = '__all__'

class ProcessConfigSerializer(serializers.ModelSerializer):
    process_name = serializers.CharField(source='process.process_name', read_only=True)
    process_code = serializers.CharField(source='process.process_code', read_only=True)
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    control_gauge_name = serializers.CharField(source='control_gauge.name', read_only=True)
    fixture_name = serializers.CharField(source='fixture.name', read_only=True)
    cycle_time = serializers.IntegerField(source='get_cycle_time', read_only=True)

    class Meta:
        model = ProcessConfig
        fields = [
            'id', 'workflow', 'process', 'process_code', 'process_name', 'version', 'status',
            'sequence_order', 'stock_code', 'tool', 'tool_name',
            'control_gauge', 'control_gauge_name', 'fixture', 'fixture_name',
            'axis_count', 'machine_time', 'setup_time', 'net_time',
            'number_of_bindings', 'effective_date', 'description',
            'cycle_time', 'created_at', 'modified_at'
        ]
        read_only_fields = ['effective_date']

    def validate(self, data):
        # Ensure at least one of tool, control_gauge, or fixture is specified
        if not any([data.get('tool'), data.get('control_gauge'), data.get('fixture')]):
            raise serializers.ValidationError(
                "At least one of tool, control gauge, or fixture must be specified"
            )
        return data

class ProductWorkflowSerializer(serializers.ModelSerializer):
    process_configs = ProcessConfigSerializer(many=True, read_only=True)
    product_code = serializers.CharField(source='product.product_code', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)

    class Meta:
        model = ProductWorkflow
        fields = [
            'id', 'product', 'product_code', 'product_name', 'version',
            'status', 'effective_date', 'notes', 'process_configs',
            'created_by', 'created_by_name', 'approved_by', 'approved_by_name',
            'approved_at', 'created_at'
        ]
        read_only_fields = ['effective_date', 'approved_at', 'created_at']

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
    process_config_details = ProcessConfigSerializer(source='process_config', read_only=True)
    machine_details = MachineSerializer(source='machine', read_only=True)
    operator_name = serializers.CharField(source='operator.get_full_name', read_only=True)

    class Meta:
        model = SubWorkOrderProcess
        fields = [
            'id', 'sub_work_order', 'process_config', 'process_config_details',
            'machine', 'machine_details', 'sequence_order', 'planned_duration_minutes',
            'actual_duration_minutes', 'status', 'start_time', 'end_time',
            'operator', 'operator_name', 'setup_time_minutes', 'notes'
        ]

class SubWorkOrderProcessCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubWorkOrderProcess
        fields = [
            'sub_work_order', 'process_config',
            'machine', 'sequence_order', 'planned_duration_minutes',
            'status', 'start_time', 'end_time', 'operator',
            'setup_time_minutes', 'notes'
        ]

    def validate(self, data):
        # Ensure process_config belongs to the workflow if both are provided
        process_config = data.get('process_config')
                
        if process_config and process_config.workflow != data.get('sub_work_order').parent_work_order.workflow:
            raise serializers.ValidationError(
                "The selected process configuration does not belong to the work order's workflow"
            )
                
        return data

class SubWorkOrderSerializer(serializers.ModelSerializer):
    processes = SubWorkOrderProcessSerializer(many=True, read_only=True)
    bom_component_details = serializers.SerializerMethodField()

    class Meta:
        model = SubWorkOrder
        fields = [
            'id', 'parent_work_order', 'bom_component', 'bom_component_details',
            'quantity', 'planned_start', 'planned_end', 'actual_start',
            'actual_end', 'status', 'output_quantity', 'scrap_quantity',
            'target_category', 'notes', 'completion_percentage', 'assigned_to',
            'processes', 'created_at', 'updated_at'
        ]

    def get_bom_component_details(self, obj):
        component = obj.bom_component
        return {
            'product_code': component.product.product_code,
            'product_name': component.product.product_name,
            'quantity': component.quantity,
            'sequence_order': component.sequence_order,
            'product_type': component.product.product_type
        }

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
    product_details = serializers.SerializerMethodField()
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)

    class Meta:
        model = WorkOrder
        fields = [
            'id', 'order_number', 'sales_order_item', 'bom', 'product_details',
            'quantity', 'planned_start', 'planned_end', 'actual_start',
            'actual_end', 'status', 'priority', 'notes', 'completion_percentage',
            'assigned_to', 'assigned_to_name', 'sub_orders', 'created_at', 'updated_at'
        ]

    def get_product_details(self, obj):
        return {
            'product_code': obj.bom.product.product_code,
            'product_name': obj.bom.product.product_name,
            'product_type': obj.bom.product.product_type,
            'bom_version': obj.bom.version
        }

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
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = WorkOrderOutput
        fields = [
            'id', 'sub_work_order', 'quantity', 'status', 'target_category',
            'notes', 'quarantine_reason', 'inspection_required', 'created_by',
            'created_by_name', 'production_date', 'created_at', 'updated_at'
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

class ProcessConfigCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessConfig
        fields = [
            'process', 'version', 'status',
            'sequence_order', 'stock_code', 'tool',
            'control_gauge', 'fixture', 'axis_count',
            'machine_time', 'setup_time', 'net_time',
            'number_of_bindings', 'description'
        ]

    def validate(self, data):
        # Ensure at least one of tool, control_gauge, or fixture is specified
        if not any([data.get('tool'), data.get('control_gauge'), data.get('fixture')]):
            raise serializers.ValidationError(
                "At least one of tool, control gauge, or fixture must be specified"
            )
        return data

class WorkflowWithConfigsSerializer(serializers.ModelSerializer):
    process_configs = ProcessConfigCreateSerializer(many=True)

    class Meta:
        model = ProductWorkflow
        fields = [
            'product', 'version', 'status',
            'notes', 'process_configs'
        ]

    def validate(self, data):
        # Check if there's already an active workflow for this product if status is ACTIVE
        if data.get('status') == 'ACTIVE':
            active_workflow = ProductWorkflow.objects.filter(
                product=data['product'],
                status='ACTIVE'
            ).exists()
            
            if active_workflow:
                raise serializers.ValidationError(
                    f"Product already has an active workflow"
                )

        # Validate uniqueness of process configs
        process_configs = data.get('process_configs', [])
        product = data['product']
        
        for config in process_configs:
            process = config.get('process')
            stock_code = config.get('stock_code')
            
            # Check if there's an existing workflow with the same process and stock_code for this product
            existing_configs = ProcessConfig.objects.filter(
                workflow__product=product,
                process=process,
                stock_code=stock_code
            )
            
            if existing_configs.exists():
                raise serializers.ValidationError(
                    f"A workflow configuration already exists for product {product.product_code} "
                    f"with process {process} and stock code {stock_code}"
                )

        return data

    @transaction.atomic
    def create(self, validated_data):
        process_configs_data = validated_data.pop('process_configs', [])
        workflow = ProductWorkflow.objects.create(**validated_data)

        for config_data in process_configs_data:
            ProcessConfig.objects.create(workflow=workflow, **config_data)

        return workflow