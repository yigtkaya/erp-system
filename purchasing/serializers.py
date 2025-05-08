# purchasing/serializers.py
from rest_framework import serializers
from .models import (
    Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseRequisition,
    PurchaseRequisitionItem, GoodsReceipt, GoodsReceiptItem,
    SupplierPriceList
)
from core.serializers import UserListSerializer
from inventory.serializers import ProductSerializer
from sales.serializers import CurrencySerializer


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id', 'code', 'name', 'contact_person', 'email', 'phone',
            'address', 'country', 'payment_terms', 'tax_id', 'is_active',
            'rating', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    extended_price = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    is_fully_received = serializers.ReadOnlyField()
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'product', 'product_id',
            'quantity_ordered', 'quantity_received', 'unit_price',
            'tax_percentage', 'expected_delivery_date', 'notes',
            'extended_price', 'tax_amount', 'total_price',
            'is_fully_received'
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
        write_only=True
    )
    currency = CurrencySerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(
        queryset=Currency.objects.all(),
        source='currency',
        write_only=True
    )
    buyer = UserListSerializer(read_only=True)
    approved_by = UserListSerializer(read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    net_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_id', 'order_date',
            'expected_delivery_date', 'status', 'currency', 'currency_id',
            'exchange_rate', 'buyer', 'approved_by', 'approval_date',
            'supplier_reference', 'shipping_address', 'billing_address',
            'payment_terms', 'notes', 'total_amount', 'tax_amount',
            'net_amount', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'buyer', 'approved_by', 'approval_date']


class PurchaseRequisitionItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    preferred_supplier = SupplierSerializer(read_only=True)
    preferred_supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='preferred_supplier',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = PurchaseRequisitionItem
        fields = [
            'id', 'requisition', 'product', 'product_id', 'quantity',
            'estimated_price', 'preferred_supplier', 'preferred_supplier_id',
            'notes'
        ]


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    requested_by = UserListSerializer(read_only=True)
    approved_by = UserListSerializer(read_only=True)
    items = PurchaseRequisitionItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = PurchaseRequisition
        fields = [
            'id', 'requisition_number', 'requested_by', 'request_date',
            'required_date', 'status', 'approved_by', 'approval_date',
            'department', 'notes', 'converted_to_po', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'requested_by', 'approved_by', 'approval_date']


class GoodsReceiptItemSerializer(serializers.ModelSerializer):
    po_item = PurchaseOrderItemSerializer(read_only=True)
    po_item_id = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrderItem.objects.all(),
        source='po_item',
        write_only=True
    )
    
    class Meta:
        model = GoodsReceiptItem
        fields = [
            'id', 'receipt', 'po_item', 'po_item_id', 'quantity_received',
            'quantity_accepted', 'quantity_rejected', 'rejection_reason',
            'storage_location', 'batch_number'
        ]


class GoodsReceiptSerializer(serializers.ModelSerializer):
    purchase_order = PurchaseOrderSerializer(read_only=True)
    purchase_order_id = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrder.objects.all(),
        source='purchase_order',
        write_only=True
    )
    received_by = UserListSerializer(read_only=True)
    items = GoodsReceiptItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = GoodsReceipt
        fields = [
            'id', 'receipt_number', 'purchase_order', 'purchase_order_id',
            'receipt_date', 'received_by', 'supplier_delivery_note',
            'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'received_by']


class SupplierPriceListSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
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
        model = SupplierPriceList
        fields = [
            'id', 'supplier', 'supplier_id', 'product', 'product_id',
            'unit_price', 'currency', 'currency_id', 'valid_from',
            'valid_until', 'minimum_quantity', 'lead_time_days',
            'is_active', 'notes', 'is_valid'
        ]