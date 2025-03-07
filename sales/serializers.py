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

    def to_representation(self, instance):
        # Ensure we have the latest data
        instance.refresh_from_db()
        return super().to_representation(instance)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value

class ShippingSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='order_item.product', read_only=True)
    
    class Meta:
        model = Shipping
        fields = ['id', 'shipping_no', 'shipping_date',
                 'order', 'order_item', 'product_details',
                 'quantity', 'package_number', 'shipping_note']
        read_only_fields = ['shipping_no']

    def create(self, validated_data):
        with atomic():
            # Extract data
            order_item = validated_data['order_item']
            quantity = validated_data['quantity']
            order = validated_data['order']
            
            print(f"\nDEBUG: Starting shipment creation for Order Item {order_item.id}")
            print(f"DEBUG: Initial state - Order Item quantity: {order_item.quantity}, fulfilled: {order_item.fulfilled_quantity}")
            
            # Create the shipping record
            shipping = Shipping.objects.create(**validated_data)
            print(f"DEBUG: Created shipping record with quantity: {quantity}")
            
            # Create inventory transaction
            InventoryTransaction.objects.create(
                product=order_item.product,
                quantity_change=-quantity,
                transaction_type='SHIPMENT',
                reference_id=shipping.id,
                notes=f"Shipment {shipping.shipping_no}",
                performed_by=validated_data.get('created_by')
            )
            
            # Get all shipments for this order item
            all_shipments = Shipping.objects.filter(order_item=order_item)
            print(f"DEBUG: All shipments for this order item:")
            for ship in all_shipments:
                print(f"DEBUG: - Shipment {ship.shipping_no}: quantity={ship.quantity}")
            
            # Get the current total shipped quantity
            total_shipped = all_shipments.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            print(f"DEBUG: Total shipped quantity calculation: {total_shipped}")
            
            # Update the order item's fulfilled quantity directly
            SalesOrderItem.objects.filter(id=order_item.id).update(
                fulfilled_quantity=total_shipped
            )
            
            # Refresh both the order item and order from the database
            order_item.refresh_from_db()
            order.refresh_from_db()
            
            print(f"DEBUG: After update - Order Item fulfilled quantity: {order_item.fulfilled_quantity}")
            
            # Check all items in the order
            print(f"\nDEBUG: Checking all items in order {order.order_number}:")
            all_items_fulfilled = True
            for item in order.items.all():
                item.refresh_from_db()
                print(f"DEBUG: Item {item.id} - Quantity: {item.quantity}, Fulfilled: {item.fulfilled_quantity}")
                if item.fulfilled_quantity < item.quantity:
                    all_items_fulfilled = False
            
            print(f"DEBUG: All items fulfilled? {all_items_fulfilled}")
            print(f"DEBUG: Current order status: {order.status}")
            
            # Update order status if needed
            if all_items_fulfilled and order.status != 'CLOSED':
                print(f"DEBUG: Setting order status to CLOSED")
                order.status = 'CLOSED'
                order.save(update_fields=['status'])
            elif not all_items_fulfilled and order.status == 'CLOSED':
                print(f"DEBUG: Setting order status to OPEN")
                order.status = 'OPEN'
                order.save(update_fields=['status'])
            
            # Refresh the shipping object to get the latest related data
            shipping = Shipping.objects.select_related(
                'order', 
                'order_item'
            ).prefetch_related(
                'order_item__product'
            ).get(id=shipping.id)
            
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

    def to_representation(self, instance):
        # Ensure we have the latest data
        instance.refresh_from_db()
        # Refresh related items
        for item in instance.items.all():
            item.refresh_from_db()
        return super().to_representation(instance)

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