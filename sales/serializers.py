# sales/serializers.py
from rest_framework import serializers
from decimal import Decimal
from .models import (
    Currency, SalesOrder, SalesOrderItem, SalesQuotation,
    SalesQuotationItem, CustomerPriceList
)
from core.serializers import CustomerSerializer, UserListSerializer
from inventory.serializers import ProductSerializer
from inventory.models import Product  # Import the Product model
from core.models import Customer  # Import the Customer model


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'code', 'name', 'symbol', 'is_active']


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    extended_price = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'sales_order', 'product', 'product_id', 'quantity',
            'unit_price', 'discount_percentage', 'tax_percentage',
            'delivery_date', 'notes', 'extended_price', 'tax_amount',
            'total_price'
        ]


class SalesOrderSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer',
        write_only=True
    )
    currency = CurrencySerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all(),
        source='currency',
        write_only=True
    )
    salesperson = UserListSerializer(read_only=True)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    net_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer', 'customer_id', 'order_date',
            'delivery_date', 'status', 'currency', 'currency_id',
            'exchange_rate', 'payment_terms', 'customer_po_number',
            'salesperson', 'shipping_address', 'billing_address', 'notes',
            'total_amount', 'tax_amount', 'discount_amount', 'net_amount',
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
    extended_price = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesQuotationItem
        fields = [
            'id', 'quotation', 'product', 'product_id', 'quantity',
            'unit_price', 'discount_percentage', 'tax_percentage',
            'notes', 'extended_price'
        ]


class SalesQuotationSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer',
        write_only=True
    )
    currency = CurrencySerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all(),
        source='currency',
        write_only=True
    )
    salesperson = UserListSerializer(read_only=True)
    items = SalesQuotationItemSerializer(many=True, read_only=True)
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = SalesQuotation
        fields = [
            'id', 'quotation_number', 'customer', 'customer_id',
            'quotation_date', 'valid_until', 'status', 'currency',
            'currency_id', 'exchange_rate', 'payment_terms',
            'salesperson', 'notes', 'total_amount', 'converted_to_order',
            'is_expired', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'salesperson']


class CustomerPriceListSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer',
        write_only=True
    )
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    currency = CurrencySerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all(),
        source='currency',
        write_only=True
    )
    is_valid = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomerPriceList
        fields = [
            'id', 'customer', 'customer_id', 'product', 'product_id',
            'unit_price', 'currency', 'currency_id', 'valid_from',
            'valid_until', 'minimum_quantity', 'discount_percentage',
            'is_active', 'notes', 'is_valid'
        ]