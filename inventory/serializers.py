# inventory/serializers.py
from rest_framework import serializers
from .models import (
    Product, RawMaterial, InventoryCategory, UnitOfMeasure, StockTransaction,
    Tool, ToolUsage, Holder, Fixture, ControlGauge, TechnicalDrawing # Added TechnicalDrawing
)
from common.models import FileVersionManager, ContentType, FileCategory # Added import

class StockTransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta:
        model = StockTransaction
        fields = [
            'id', 'transaction_date', 'transaction_type', 'transaction_type_display',
            'quantity', 'unit_cost', 'category_name', 'location', 'batch_number',
            'reference', 'notes', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['created_at']

class TechnicalDrawingSerializer(serializers.ModelSerializer):
    drawing_url = serializers.SerializerMethodField()
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)

    class Meta:
        model = TechnicalDrawing
        fields = [
            'id', 'version', 'drawing_code', 'effective_date', 'is_current',
            'revision_notes', 'approved_by_username', 'approved_at', 'drawing_url',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['created_at', 'modified_at']

    def get_drawing_url(self, obj):
        # Assuming TechnicalDrawing model has a 'drawing_file' property or similar
        # that returns the FileVersionManager instance for the current drawing.
        # And that FileVersionManager instance has a 'file.url' attribute for the R2 URL.
        drawing_file_version = obj.drawing_file # This is a property in TechnicalDrawing model
        if drawing_file_version and hasattr(drawing_file_version, 'file') and hasattr(drawing_file_version.file, 'url'):
            return drawing_file_version.file.url
        return None

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    
    inventory_category_name = serializers.CharField(source='inventory_category.name', read_only=True)
    unit_of_measure_name = serializers.CharField(source='unit_of_measure.unit_name', read_only=True)
    # The existing technical_image is for upload, let's keep it if needed for that purpose,
    # but we will add a new field for displaying the R2 image from TechnicalDrawing.
    # technical_image = serializers.ImageField(write_only=True, required=False, allow_null=True) 
    
    current_technical_drawing = serializers.SerializerMethodField()
    transactions = StockTransactionSerializer(many=True, read_only=True)


    class Meta:
        model = Product
        fields = '__all__' # Keep this for now, can be refined later
        # Explicitly list fields to ensure new ones are included if not using '__all__'
        # fields = [
        #     'id', 'product_code', 'product_name', 'project_name', 'product_type', 
        #     'multicode', 'description', 'current_stock', 'reserved_stock', 
        #     'unit_of_measure', 'unit_of_measure_name', 'customer', 
        #     'inventory_category', 'inventory_category_name', 'is_active', 'tags', 
        #     'reorder_point', 'lead_time_days', 'available_stock',
        #     'current_technical_drawing', 'transactions',
        #     'created_at', 'modified_at', 
        #     # 'technical_image' # This is the write_only field for upload
        # ]
        read_only_fields = ['created_at', 'modified_at', 'available_stock']
        extra_kwargs = {
            'product_code': {'min_length': 3},
            'reorder_point': {'min_value': 0}
        }

    def get_current_technical_drawing(self, obj):
        # Fetch the current technical drawing for the product
        current_drawing = obj.technical_drawings.filter(is_current=True).first()
        if current_drawing:
            # Pass the request from the ProductSerializer context to the TechnicalDrawingSerializer context
            context = self.context 
            return TechnicalDrawingSerializer(current_drawing, context=context).data
        return None

    def create(self, validated_data):
        # image_file = validated_data.pop('technical_image', None) # Keep if general product image upload is still desired
        product = super().create(validated_data)
        # if image_file:
        #     user = self.context['request'].user if 'request' in self.context and hasattr(self.context['request'], 'user') else None
        #     user = user if user and not user.is_anonymous else None
        #     FileVersionManager.create_version(
        #         file=image_file,
        #         content_type=ContentType.PRODUCT_IMAGE, # This was for general product image
        #         object_id=str(product.id),
        #         file_category=FileCategory.PRODUCT,
        #         user=user,
        #         notes="Initial product image upload."
        #     )
        return product

class RawMaterialSerializer(serializers.ModelSerializer):
    available_stock = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    unit_name = serializers.CharField(source='unit.unit_name', read_only=True)
    category_name = serializers.CharField(source='inventory_category.name', read_only=True)
    technical_image = serializers.ImageField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = RawMaterial
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at', 'available_stock']
        extra_kwargs = {
            'material_code': {'min_length': 3},
            'width': {'min_value': 0.01},
            'height': {'min_value': 0.01},
            'thickness': {'min_value': 0.01}
        }

    def create(self, validated_data):
        image_file = validated_data.pop('technical_image', None)
        raw_material = super().create(validated_data)
        if image_file:
            user = self.context['request'].user if 'request' in self.context and hasattr(self.context['request'], 'user') else None
            # Ensure user is not AnonymousUser, or pass None
            user = user if user and not user.is_anonymous else None
            FileVersionManager.create_version(
                file=image_file,
                content_type=ContentType.MATERIAL_IMAGE,
                object_id=str(raw_material.id),
                file_category=FileCategory.PRODUCT, # Using PRODUCT category for material images too
                user=user,
                notes="Initial raw material image upload."
            )
        return raw_material

class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'modified_at']

class ToolUsageSerializer(serializers.ModelSerializer):
    tool_stock_code = serializers.CharField(source='tool.stock_code', read_only=True)
    issued_by_username = serializers.CharField(source='issued_by.username', read_only=True, allow_null=True)
    returned_to_username = serializers.CharField(source='returned_to.username', read_only=True, allow_null=True)
    # work_order_number = serializers.CharField(source='work_order.work_order_number', read_only=True, allow_null=True) # If work_order is added back

    class Meta:
        model = ToolUsage
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'modified_at']

class HolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holder
        fields = [
            'id', 'stock_code', 'supplier_name', 'product_code', 'unit_price_tl',
            'unit_price_euro', 'unit_price_usd', 'holder_type', 'pulley_type',
            'water_cooling', 'distance_cooling', 'tool_connection_diameter',
            'holder_type_enum', 'status', 'row', 'column', 'table_id',
            'description', 'quantity', 'created_at', 'modified_at'
        ]
        read_only_fields = ['id', 'created_at', 'modified_at']

class FixtureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fixture
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at']

class ControlGaugeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlGauge
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at'] 