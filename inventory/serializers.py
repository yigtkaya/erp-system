from rest_framework import serializers
from .models import (
    InventoryCategory, UnitOfMeasure, Product,
    TechnicalDrawing, RawMaterial, InventoryTransaction
)

class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = ['id', 'name', 'description']

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'unit_code', 'unit_name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'product_code', 'product_name', 'product_type',
            'description', 'current_stock', 'customer',
            'inventory_category', 'created_at', 'modified_at'
        ]

class TechnicalDrawingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalDrawing
        fields = [
            'id', 'product', 'version', 'drawing_code', 'drawing_url',
            'effective_date', 'is_current', 'revision_notes', 'approved_by',
            'created_at', 'modified_at'
        ]

class RawMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawMaterial
        fields = [
            'id', 'material_code', 'material_name', 'current_stock',
            'unit', 'inventory_category', 'created_at', 'modified_at'
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