from rest_framework import serializers
from erp_core.models import Customer
from inventory.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at']

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'code', 'name', 
            'created_at', 'modified_at',
            'created_by', 'modified_by'
        ]
        read_only_fields = [
            'created_at', 'modified_at',
            'created_by', 'modified_by'
        ]
    
    def validate_code(self, value):
        if not value.isalnum():
            raise serializers.ValidationError("Customer code must be alphanumeric")
        return value