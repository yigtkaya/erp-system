from rest_framework import serializers
from .models import (
    InventoryCategory, UnitOfMeasure, Product,
    TechnicalDrawing, RawMaterial, InventoryTransaction,
    Tool, Holder, Fixture, ControlGauge
)
from erp_core.serializers import UserSerializer, CustomerSerializer
from django.core.exceptions import ObjectDoesNotExist

class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = ['id', 'name', 'description']

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'unit_code', 'unit_name']

class TechnicalDrawingListSerializer(serializers.ModelSerializer):
    drawing_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TechnicalDrawing
        fields = [
            'id', 'version', 'drawing_code', 'drawing_file',
            'drawing_url', 'effective_date', 'is_current', 'revision_notes',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['drawing_url']

    def get_drawing_url(self, obj):
        return obj.drawing_url

class ProductSerializer(serializers.ModelSerializer):
    technical_drawings = TechnicalDrawingListSerializer(source='technicaldrawing_set', many=True, read_only=True)
    inventory_category_display = serializers.CharField(source='inventory_category.get_name_display', read_only=True)
    in_process_quantity_by_process = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'product_code', 'product_name', 'product_type',
            'description', 'current_stock', 'multicode', 'project_name',
            'inventory_category', 'inventory_category_display',
            'technical_drawings', 'created_at', 'modified_at', 'in_process_quantity_by_process'
        ]

    def get_in_process_quantity_by_process(self, obj):
        return obj.in_process_quantity_by_process

class TechnicalDrawingDetailSerializer(serializers.ModelSerializer):
    drawing_url = serializers.SerializerMethodField()
    product_code = serializers.CharField(source='product.product_code', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    
    class Meta:
        model = TechnicalDrawing
        fields = [
            'id', 'product', 'product_code', 'product_name', 'version', 
            'drawing_code', 'drawing_file', 'drawing_url', 'effective_date', 
            'is_current', 'revision_notes', 'approved_by', 'created_at', 'modified_at'
        ]
        read_only_fields = ['drawing_url', 'product_code', 'product_name']

    def get_drawing_url(self, obj):
        return obj.drawing_url

class RawMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMaterial
        fields = [
            'id',
            'material_code',
            'material_name',
            'current_stock',
            'unit',
            'inventory_category',
            'material_type',
            'width',
            'height',
            'thickness',
            'diameter_mm',
            'created_at',
            'modified_at'
        ]

class InventoryTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'product', 'material', 'quantity_change', 'transaction_type',
            'transaction_date', 'performed_by', 'verified_by', 'notes',
            'from_category', 'to_category'
        ]
        read_only_fields = ['transaction_date', 'performed_by']

    def validate(self, data):
        if bool(data.get('product')) == bool(data.get('material')):
            raise serializers.ValidationError("Either product or material must be set, but not both.")
        
        if data.get('transaction_type') == 'TRANSFER':
            if not data.get('from_category') or not data.get('to_category'):
                raise serializers.ValidationError("Category transfer requires both from and to categories")
            
            if data.get('product'):
                allowed_categories = self._get_allowed_categories(data['product'].product_type)
                if data['to_category'].name not in allowed_categories:
                    raise serializers.ValidationError(f"Invalid category transfer for product type {data['product'].product_type}")
            
            if data.get('material') and data['to_category'].name not in ['HAMMADDE', 'HURDA', 'KARANTINA']:
                raise serializers.ValidationError("Invalid category transfer for raw material")
        
        return data

    def _get_allowed_categories(self, product_type):
        if product_type == 'SINGLE':
            return ['HAMMADDE', 'HURDA', 'KARANTINA']
        elif product_type == 'SEMI':
            return ['PROSES', 'MAMUL', 'KARANTINA', 'HURDA']
        else:  # MONTAGED
            return ['MAMUL', 'KARANTINA', 'HURDA']

class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = '__all__'
        read_only_fields = ('updated_at',)

class HolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Holder
        fields = '__all__'
        read_only_fields = ('updated_at',) 


class FixtureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fixture
        fields = '__all__'
        read_only_fields = ('updated_at',) 

class ControlGaugeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ControlGauge
        fields = '__all__'
        read_only_fields = ('updated_at',) 
