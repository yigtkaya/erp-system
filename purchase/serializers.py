from rest_framework import serializers
from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from inventory.serializers import ProductSerializer

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'code', 'contact_email', 'payment_terms', 'created_at', 'modified_at']
        read_only_fields = ['created_at', 'modified_at']

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'unit_price', 'received_quantity', 'created_at', 'modified_at']
        read_only_fields = ['received_quantity', 'created_at', 'modified_at']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = ['id', 'order_number', 'supplier', 'supplier_id', 'expected_delivery', 'status', 'items', 'created_at', 'modified_at']
        read_only_fields = ['order_number', 'status', 'created_at', 'modified_at'] 