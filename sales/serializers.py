# sales/serializers.py
from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem, SalesQuotation, SalesQuotationItem
from core.serializers import CustomerSerializer, UserListSerializer
from inventory.serializers import ProductSerializer
from inventory.models import Product
from core.models import Customer


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'sales_order', 'product', 'product_id', 'quantity',
            'delivery_date', 'notes'
        ]


class SalesOrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer',
        write_only=True
    )
    salesperson = UserListSerializer(read_only=True)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer', 'customer_id', 'order_date',
            'delivery_date', 'status', 'customer_po_number',
            'salesperson', 'shipping_address', 'billing_address', 'notes',
            'is_overdue', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'salesperson']


class SalesQuotationItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    
    class Meta:
        model = SalesQuotationItem
        fields = [
            'id', 'quotation', 'product', 'product_id', 'quantity', 'notes'
        ]


class SalesQuotationSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer',
        write_only=True
    )
    salesperson = UserListSerializer(read_only=True)
    items = SalesQuotationItemSerializer(many=True, read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesQuotation
        fields = [
            'id', 'quotation_number', 'customer', 'customer_id',
            'quotation_date', 'valid_until', 'status',
            'salesperson', 'notes', 'converted_to_order',
            'is_expired', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'salesperson']