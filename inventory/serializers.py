# inventory/serializers.py
from rest_framework import serializers
from .models import Product, RawMaterial, InventoryCategory, UnitOfMeasure, StockTransaction

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    
    inventory_category_name = serializers.CharField(source='inventory_category.name', read_only=True)
    unit_of_measure_name = serializers.CharField(source='unit_of_measure.unit_name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at', 'available_stock']
        extra_kwargs = {
            'product_code': {'min_length': 3},
            'reorder_point': {'min_value': 0}
        }

class RawMaterialSerializer(serializers.ModelSerializer):
    available_stock = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    unit_name = serializers.CharField(source='unit.unit_name', read_only=True)
    category_name = serializers.CharField(source='inventory_category.name', read_only=True)
    
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