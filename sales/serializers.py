from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem, Shipping, ShipmentItem
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

class ShipmentItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = ShipmentItem
        fields = ['id', 'order_item', 'product', 'product_details', 'quantity', 
                 'package_number', 'lot_number', 'serial_numbers']
        read_only_fields = ['product']

    def validate(self, data):
        # Validate that product is in MAMUL category
        order_item = data.get('order_item')
        if order_item and (not order_item.product.inventory_category or order_item.product.inventory_category.name != 'MAMUL'):
            raise serializers.ValidationError("Can only ship products from MAMUL category")
        return data

class ShippingSerializer(serializers.ModelSerializer):
    items = ShipmentItemSerializer(many=True)

    class Meta:
        model = Shipping
        fields = ['id', 'shipping_no', 'shipping_date', 'shipping_amount', 
                 'order', 'shipping_note', 'items']
        read_only_fields = ['shipping_no']

    def validate_shipping_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Shipping amount must be greater than zero")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        with atomic():
            shipping = Shipping.objects.create(**validated_data)
            
            for item_data in items_data:
                order_item = item_data['order_item']
                product = order_item.product
                quantity = item_data['quantity']
                
                # Check stock availability
                if product.current_stock < quantity:
                    raise ValidationError(f"Insufficient stock for product {product.product_code}")
                
                # Calculate total shipped quantity including this shipment
                total_shipped = (
                    ShipmentItem.objects
                    .filter(order_item=order_item)
                    .aggregate(total=Sum('quantity'))['total'] or 0
                ) + quantity

                # Validate against order quantity
                if total_shipped > order_item.quantity:
                    raise ValidationError(f"Total shipped quantity ({total_shipped}) would exceed ordered quantity ({order_item.quantity})")
                
                # Create shipment item
                shipment_item = ShipmentItem.objects.create(
                    shipment=shipping,
                    **item_data
                )
                
                # Update product stock
                product.current_stock = F('current_stock') - quantity
                product.save(update_fields=['current_stock'])
                
                # Update fulfilled quantity using F() expression
                order_item.fulfilled_quantity = total_shipped
                order_item.save(update_fields=['fulfilled_quantity'])
                
                # Create inventory transaction
                InventoryTransaction.objects.create(
                    product=product,
                    quantity_change=-quantity,
                    transaction_type='SHIPMENT',
                    reference_id=shipment_item.id,
                    notes=f"Shipment {shipping.shipping_no}",
                    performed_by=validated_data['created_by']
                )
            
            # Check if order is fully fulfilled and update status if needed
            order = validated_data['order']
            all_items_fulfilled = all(
                item.fulfilled_quantity == item.quantity 
                for item in order.items.all()
            )
            if all_items_fulfilled and order.status != 'COMPLETED':
                order.status = 'COMPLETED'
                order.save(update_fields=['status'])
            
            return shipping

class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True)
    shipments = ShippingSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_number = serializers.CharField(read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = ['id', 'order_number', 'customer', 'customer_name', 'order_date', 
                 'order_receiving_date', 'deadline_date', 'kapsam_deadline_date',
                 'approved_by', 'status', 'status_display', 'items', 'shipments']
        read_only_fields = ['order_number']

    def get_total_shipped_amount(self, obj):
        """Calculate total shipped quantity across all shipments"""
        return sum(shipping.quantity for shipping in obj.shipments.all())

    def validate(self, data):
        # Validate dates
        order_receiving_date = data.get('order_receiving_date')
        deadline_date = data.get('deadline_date')
        kapsam_deadline_date = data.get('kapsam_deadline_date')
        status = data.get('status')

        # Validate required fields for APPROVED status
        if status == 'APPROVED':
            if not order_receiving_date:
                raise serializers.ValidationError(
                    {"order_receiving_date": "Order receiving date is required for approved orders"}
                )
            if not kapsam_deadline_date:
                raise serializers.ValidationError(
                    {"kapsam_deadline_date": "Kapsam deadline date is required for approved orders"}
                )

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
        
        # Set approved_by if status is APPROVED
        if validated_data.get('status') == 'APPROVED':
            validated_data['approved_by'] = request.user if request else None
        
        sales_order = SalesOrder.objects.create(**validated_data)
        
        for item_data in items_data:
            SalesOrderItem.objects.create(sales_order=sales_order, **item_data)
        
        return sales_order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        request = self.context.get('request')
        
        # Set approved_by if status is changing to APPROVED
        if validated_data.get('status') == 'APPROVED' and instance.status != 'APPROVED':
            validated_data['approved_by'] = request.user if request else None
        
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