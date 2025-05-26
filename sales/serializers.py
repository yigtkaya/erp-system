# sales/serializers.py
from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem, SalesQuotation, SalesQuotationItem, OrderItemStatus
from core.serializers import CustomerSerializer, UserListSerializer
from inventory.serializers import ProductSerializer
from inventory.models import Product
from core.models import Customer
from django.utils import timezone
from datetime import datetime


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


# Enhanced Batch Operation Serializers

class BatchDeleteSerializer(serializers.Serializer):
    """Serializer for batch delete operations"""
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of item IDs to delete"
    )
    confirm_deletion = serializers.BooleanField(
        default=False,
        help_text="Must be true to confirm deletion"
    )
    
    def validate_confirm_deletion(self, value):
        if not value:
            raise serializers.ValidationError("You must confirm deletion by setting confirm_deletion to true")
        return value


class BatchUpdateSerializer(serializers.Serializer):
    """Enhanced serializer for batch update operations"""
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of item IDs to update"
    )
    update_data = serializers.DictField(
        help_text="Fields to update"
    )
    
    def validate_update_data(self, value):
        allowed_fields = [
            'delivery_date', 'kapsam_deadline_date', 'notes', 
            'quantity', 'status', 'order_date'
        ]
        invalid_fields = set(value.keys()) - set(allowed_fields)
        
        if invalid_fields:
            raise serializers.ValidationError(
                f"Invalid fields: {', '.join(invalid_fields)}. "
                f"Allowed fields: {', '.join(allowed_fields)}"
            )
        
        # Validate status if provided
        if 'status' in value:
            if value['status'] not in [choice[0] for choice in OrderItemStatus.choices]:
                raise serializers.ValidationError(
                    f"Invalid status. Valid options: {[choice[0] for choice in OrderItemStatus.choices]}"
                )
        
        # Validate quantity if provided
        if 'quantity' in value:
            try:
                quantity = int(value['quantity'])
                if quantity <= 0:
                    raise serializers.ValidationError("Quantity must be a positive integer")
                value['quantity'] = quantity
            except (ValueError, TypeError):
                raise serializers.ValidationError("Quantity must be a valid integer")
        
        # Validate dates if provided
        for date_field in ['delivery_date', 'kapsam_deadline_date', 'order_date']:
            if date_field in value:
                try:
                    if isinstance(value[date_field], str):
                        value[date_field] = datetime.strptime(value[date_field], '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    raise serializers.ValidationError(f"{date_field} must be in YYYY-MM-DD format")
        
        return value


class BatchAddItemSerializer(serializers.Serializer):
    """Serializer for batch adding items to a sales order"""
    sales_order_id = serializers.IntegerField(
        help_text="Sales order ID to add items to"
    )
    items = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        help_text="List of items to add"
    )
    
    def validate_sales_order_id(self, value):
        try:
            sales_order = SalesOrder.objects.get(id=value)
        except SalesOrder.DoesNotExist:
            raise serializers.ValidationError("Sales order not found")
        return value
    
    def validate_items(self, value):
        required_fields = ['product_id', 'quantity', 'delivery_date']
        optional_fields = ['order_date', 'kapsam_deadline_date', 'notes', 'status']
        
        validated_items = []
        
        for i, item in enumerate(value):
            # Check required fields
            missing_fields = set(required_fields) - set(item.keys())
            if missing_fields:
                raise serializers.ValidationError(
                    f"Item {i+1}: Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Check for invalid fields
            all_allowed_fields = required_fields + optional_fields
            invalid_fields = set(item.keys()) - set(all_allowed_fields)
            if invalid_fields:
                raise serializers.ValidationError(
                    f"Item {i+1}: Invalid fields: {', '.join(invalid_fields)}"
                )
            
            # Validate product exists
            try:
                product = Product.objects.get(id=item['product_id'])
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Item {i+1}: Product with ID {item['product_id']} not found")
            
            # Validate quantity
            try:
                quantity = int(item['quantity'])
                if quantity <= 0:
                    raise serializers.ValidationError(f"Item {i+1}: Quantity must be positive")
                item['quantity'] = quantity
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Item {i+1}: Invalid quantity")
            
            # Validate dates
            for date_field in ['delivery_date', 'order_date', 'kapsam_deadline_date']:
                if date_field in item:
                    try:
                        if isinstance(item[date_field], str):
                            item[date_field] = datetime.strptime(item[date_field], '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        raise serializers.ValidationError(
                            f"Item {i+1}: {date_field} must be in YYYY-MM-DD format"
                        )
            
            # Set default values
            if 'order_date' not in item:
                item['order_date'] = timezone.now().date()
            
            if 'status' not in item:
                item['status'] = OrderItemStatus.DRAFT
            else:
                # Validate status
                if item['status'] not in [choice[0] for choice in OrderItemStatus.choices]:
                    raise serializers.ValidationError(
                        f"Item {i+1}: Invalid status. Valid options: {[choice[0] for choice in OrderItemStatus.choices]}"
                    )
            
            # Validate date logic
            if item['delivery_date'] < item['order_date']:
                raise serializers.ValidationError(
                    f"Item {i+1}: Delivery date cannot be before order date"
                )
            
            if 'kapsam_deadline_date' in item and item['kapsam_deadline_date']:
                if item['kapsam_deadline_date'] < item['order_date']:
                    raise serializers.ValidationError(
                        f"Item {i+1}: Kapsam deadline cannot be before order date"
                    )
            
            validated_items.append(item)
        
        return validated_items


class BatchRescheduleSerializer(serializers.Serializer):
    """Enhanced serializer for batch rescheduling operations"""
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of item IDs to reschedule"
    )
    days_offset = serializers.IntegerField(
        help_text="Number of days to offset (positive for future, negative for past)"
    )
    update_kapsam = serializers.BooleanField(
        default=True,
        help_text="Whether to also update kapsam deadline dates"
    )


class BatchStatusUpdateSerializer(serializers.Serializer):
    """Serializer for batch status updates"""
    item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of item IDs to update status"
    )
    new_status = serializers.ChoiceField(
        choices=OrderItemStatus.choices,
        help_text="New status for all items"
    )
    force_update = serializers.BooleanField(
        default=False,
        help_text="Force status update even if it doesn't follow normal progression"
    )


class BatchOperationResponseSerializer(serializers.Serializer):
    """Serializer for batch operation responses"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    affected_count = serializers.IntegerField()
    details = serializers.DictField(required=False)
    errors = serializers.ListField(child=serializers.CharField(), required=False)