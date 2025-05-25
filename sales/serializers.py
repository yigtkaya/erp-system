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
    is_overdue = serializers.ReadOnlyField()
    is_kapsam_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'sales_order', 'product', 'product_id', 'quantity', 'status',
            'order_date', 'delivery_date', 'kapsam_deadline_date', 'notes',
            'is_overdue', 'is_kapsam_overdue'
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
    status = serializers.ReadOnlyField()
    status_summary = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    is_kapsam_overdue = serializers.ReadOnlyField()
    earliest_delivery_date = serializers.ReadOnlyField()
    earliest_kapsam_deadline = serializers.ReadOnlyField()
    latest_kapsam_deadline = serializers.ReadOnlyField()
    kapsam_status = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer', 'customer_id',
            'status', 'status_summary', 'customer_po_number',
            'salesperson', 'shipping_address', 'billing_address', 'notes',
            'is_overdue', 'is_kapsam_overdue', 'earliest_delivery_date', 
            'earliest_kapsam_deadline', 'latest_kapsam_deadline', 'kapsam_status',
            'items', 'created_at', 'updated_at'
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


class BatchUpdateSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    update_data = serializers.DictField()
    
    def validate_update_data(self, value):
        allowed_fields = ['delivery_date', 'kapsam_deadline_date', 'notes', 'quantity']
        invalid_fields = set(value.keys()) - set(allowed_fields)
        
        if invalid_fields:
            raise serializers.ValidationError(
                f"Invalid fields: {', '.join(invalid_fields)}. "
                f"Allowed fields: {', '.join(allowed_fields)}"
            )
        
        return value


class BatchRescheduleSerializer(serializers.Serializer):
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    days_offset = serializers.IntegerField()