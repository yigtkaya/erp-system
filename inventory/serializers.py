# inventory/serializers.py
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at'] 