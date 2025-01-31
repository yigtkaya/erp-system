from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem
from inventory.serializers import ProductSerializer

class SalesOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'product', 'quantity', 'fulfilled_quantity',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['fulfilled_quantity']

class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer', 'order_date',
            'deadline_date', 'approved_by', 'status', 'items',
            'created_at', 'modified_at'
        ]
        read_only_fields = ['order_number', 'status']

    def validate_deadline_date(self, value):
        if value < self.initial_data.get('order_date'):
            raise serializers.ValidationError(
                "Deadline date cannot be before order date"
            )
        return value 