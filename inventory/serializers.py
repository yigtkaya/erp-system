# inventory/serializers.py
from rest_framework import serializers
from .models import (
    Product, RawMaterial, InventoryCategory, UnitOfMeasure, StockTransaction,
    Tool, ToolUsage, Holder, Fixture, ControlGauge # Added Tool, ToolUsage and uncommented others
)
from common.models import FileVersionManager, ContentType, FileCategory # Added import

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    
    inventory_category_name = serializers.CharField(source='inventory_category.name', read_only=True)
    unit_of_measure_name = serializers.CharField(source='unit_of_measure.unit_name', read_only=True)
    technical_image = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at', 'available_stock']
        extra_kwargs = {
            'product_code': {'min_length': 3},
            'reorder_point': {'min_value': 0}
        }

    def create(self, validated_data):
        image_file = validated_data.pop('technical_image', None)
        product = super().create(validated_data)
        if image_file:
            user = self.context['request'].user if 'request' in self.context and hasattr(self.context['request'], 'user') else None
            # Ensure user is not AnonymousUser, or pass None
            user = user if user and not user.is_anonymous else None
            FileVersionManager.create_version(
                file=image_file,
                content_type=ContentType.PRODUCT_IMAGE,
                object_id=str(product.id),
                file_category=FileCategory.PRODUCT,
                user=user,
                notes="Initial product image upload."
            )
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
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at']

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