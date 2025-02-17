from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem, Shipping
from inventory.models import Product
from erp_core.models import Customer

class ShippingSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    delivery_status = serializers.CharField(read_only=True)
    transit_time = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Shipping
        fields = [
            'id', 'shipping_no', 'shipping_date', 'shipping_amount', 'shipping_note',
            'status', 'status_display', 'delivery_status', 'transit_time',
            'tracking_number', 'estimated_delivery_date', 'actual_delivery_date',
            'carrier', 'carrier_service',
            'package_weight', 'package_length', 'package_width', 'package_height',
            'shipping_address_line1', 'shipping_address_line2', 'shipping_city',
            'shipping_state', 'shipping_country', 'shipping_postal_code',
            'is_insured', 'insurance_amount'
        ]
        read_only_fields = ['shipping_no']

    def validate(self, data):
        # Validate insurance amount if shipment is insured
        if data.get('is_insured') and not data.get('insurance_amount'):
            raise serializers.ValidationError(
                {"insurance_amount": "Insurance amount is required for insured shipments"}
            )
        return data

class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = SalesOrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'fulfilled_quantity']
        read_only_fields = ['fulfilled_quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value

class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    shipments = ShippingSerializer(many=True, read_only=True)
    total_shipped_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer', 'customer_name',
            'order_date', 'deadline_date', 'status', 'status_display',
            'approved_by', 'items', 'shipments', 'total_shipped_amount'
        ]
        read_only_fields = ['order_number', 'approved_by', 'order_date']

    def get_total_shipped_amount(self, obj):
        """Calculate total shipped quantity across all shipments"""
        return sum(shipping.quantity for shipping in obj.shipments.all())

    def validate_deadline_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Deadline date cannot be in the past")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sales_order = SalesOrder.objects.create(**validated_data)
        
        for item_data in items_data:
            SalesOrderItem.objects.create(sales_order=sales_order, **item_data)
        
        return sales_order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        
        # Update SalesOrder fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if items_data is not None:
            # Remove existing items not in the update data
            instance.items.all().delete()
            
            # Create new items
            for item_data in items_data:
                SalesOrderItem.objects.create(sales_order=instance, **item_data)
        
        return instance 