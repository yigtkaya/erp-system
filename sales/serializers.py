from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem, Shipping
from inventory.serializers import ProductSerializer
from inventory.models import Product, InventoryTransaction
from erp_core.models import Customer
from django.db.models.deletion import ProtectedError
from django.core.exceptions import ValidationError
from django.db import transaction, models
from django.db.transaction import atomic
from django.db.models import F, Sum

class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = SalesOrderItem
        fields = ['id', 'product', 'product_details', 'quantity', 'fulfilled_quantity']
        read_only_fields = ['fulfilled_quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value

class ShippingSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = Shipping
        fields = ['id', 'shipping_no', 'shipping_date', 'shipping_amount', 
                 'order', 'order_item', 'product', 'product_details',
                 'quantity', 'package_number', 'shipping_note']
        read_only_fields = ['shipping_no', 'product']

    def validate(self, data):
        # Validate that product matches order_item's product
        order_item = data.get('order_item')
        if order_item and order_item.product != data.get('product'):
            data['product'] = order_item.product

        return data

    def create(self, validated_data):
        with atomic():
            shipping = Shipping.objects.create(**validated_data)
            
            # Update fulfilled quantity
            order_item = validated_data['order_item']
            quantity = validated_data['quantity']
            
            # Calculate total shipped quantity including this shipment
            total_shipped = (
                Shipping.objects
                .filter(order_item=order_item)
                .aggregate(total=Sum('quantity'))['total'] or 0
            )
            
            # Update fulfilled quantity
            order_item.fulfilled_quantity = total_shipped
            order_item.save(update_fields=['fulfilled_quantity'])
            
            # Create inventory transaction
            InventoryTransaction.objects.create(
                product=shipping.product,
                quantity_change=-quantity,
                transaction_type='SHIPMENT',
                reference_id=shipping.id,
                notes=f"Shipment {shipping.shipping_no}",
                performed_by=validated_data.get('created_by')
            )
            
            # Check if order is fully fulfilled and update status if needed
            order = validated_data['order']
            all_items_fulfilled = all(
                item.fulfilled_quantity == item.quantity 
                for item in order.items.all()
            )
            if all_items_fulfilled and order.status != 'CLOSED':
                order.status = 'CLOSED'
                order.save(update_fields=['status'])
            
            return shipping

class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True)
    shipments = ShippingSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = ['id', 'order_number', 'customer', 'customer_name', 'order_date', 
                 'order_receiving_date', 'deadline_date', 'kapsam_deadline_date',
                 'approved_by', 'status', 'status_display', 'items', 'shipments']

    def validate(self, data):
        # Validate dates
        order_receiving_date = data.get('order_receiving_date')
        deadline_date = data.get('deadline_date')
        kapsam_deadline_date = data.get('kapsam_deadline_date')

        # Validate date order
        if order_receiving_date and deadline_date and order_receiving_date > deadline_date:
            raise serializers.ValidationError(
                {"order_receiving_date": "Order receiving date cannot be later than deadline date"}
            )

        if kapsam_deadline_date and deadline_date and kapsam_deadline_date > deadline_date:
            raise serializers.ValidationError(
                {"kapsam_deadline_date": "Kapsam deadline date cannot be later than main deadline date"}
            )

        if order_receiving_date and kapsam_deadline_date and order_receiving_date > kapsam_deadline_date:
            raise serializers.ValidationError(
                {"order_receiving_date": "Order receiving date cannot be later than kapsam deadline date"}
            )

        return data

    def validate_deadline_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Deadline date cannot be in the past")
        return value

    def validate_kapsam_deadline_date(self, value):
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Kapsam deadline date cannot be in the past")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        
        sales_order = SalesOrder.objects.create(**validated_data)
        
        for item_data in items_data:
            SalesOrderItem.objects.create(sales_order=sales_order, **item_data)
        
        return sales_order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        request = self.context.get('request')
        
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