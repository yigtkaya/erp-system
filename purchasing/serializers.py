# purchasing/serializers.py
from rest_framework import serializers
from .models import (
    Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseRequisition,
    PurchaseRequisitionItem, GoodsReceipt, GoodsReceiptItem,
    SupplierProductInfo
)
from core.serializers import UserListSerializer
from inventory.serializers import ProductSerializer
from inventory.models import Product


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            'id', 'code', 'name', 'contact_person', 'email', 'phone',
            'address', 'country', 'tax_id', 'is_active',
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
    is_fully_received = serializers.ReadOnlyField()
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'product', 'product_id',
            'quantity_ordered', 'quantity_received', 'expected_delivery_date', 
            'notes', 'is_fully_received'
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
        write_only=True
    )
    buyer = UserListSerializer(read_only=True)
    approved_by = UserListSerializer(read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'supplier', 'supplier_id', 'order_date',
            'expected_delivery_date', 'status', 'buyer', 'approved_by', 
            'approval_date', 'supplier_reference', 'shipping_address', 
            'billing_address', 'notes', 'items', 'created_at', 'updated_at'
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
            'preferred_supplier', 'preferred_supplier_id', 'notes'
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


class SupplierProductInfoSerializer(serializers.ModelSerializer):
    """Serializer for supplier product information without pricing"""
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
    
    class Meta:
        model = SupplierProductInfo
        fields = [
            'id', 'supplier', 'supplier_id', 'product', 'product_id',
            'supplier_product_code', 'minimum_quantity', 'lead_time_days',
            'is_active', 'notes'
        ]