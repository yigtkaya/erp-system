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
from dateutil.parser import parse

class DateTimeToDateField(serializers.DateField):
    """Handles both date and datetime input while storing as date"""
    def to_internal_value(self, value):
        try:
            # Try parsing as date first
            return super().to_internal_value(value)
        except serializers.ValidationError:
            # If date parse fails, try parsing as datetime
            if isinstance(value, str):
                try:
                    dt = parse(value)
                    if dt:
                        return dt.date()
                except ValueError:
                    pass
            raise serializers.ValidationError(
                f'Date format error. Use YYYY-MM-DD or ISO datetime. Received: {value}'
            )

    def to_representation(self, value):
        # Always return ISO date format string
        return value.isoformat() if value else None

class SalesOrderItemSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='sales_order.id', read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)
    receiving_date = DateTimeToDateField(required=False, allow_null=True)
    deadline_date = DateTimeToDateField(required=False, allow_null=True)
    kapsam_deadline_date = DateTimeToDateField(required=False, allow_null=True)
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'id',
            'order_number',
            'product',
            'product_details',
            'ordered_quantity',
            'fulfilled_quantity',
            'receiving_date',
            'deadline_date',
            'kapsam_deadline_date'
        ]
        read_only_fields = ['fulfilled_quantity', 'product']

    def to_representation(self, instance):
        instance.refresh_from_db()
        return super().to_representation(instance)

    def validate(self, data):
        # Add custom date validation
        receiving_date = data.get('receiving_date')
        deadline_date = data.get('deadline_date')
        kapsam_date = data.get('kapsam_deadline_date')

        if receiving_date and deadline_date and receiving_date > deadline_date:
            raise serializers.ValidationError({
                'receiving_date': 'Receiving date cannot be after deadline date'
            })

        if receiving_date and kapsam_date and receiving_date > kapsam_date:
            raise serializers.ValidationError({
                'receiving_date': 'Receiving date cannot be after kapsam deadline date'
            })

        return data

    def validate_ordered_quantity(self, value):
        instance = self.instance
        if instance and value < instance.fulfilled_quantity:
            raise serializers.ValidationError(
                f"Ordered quantity cannot be less than fulfilled quantity ({instance.fulfilled_quantity})"
            )
        return value


class ShippingSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='order_item.product', read_only=True)
    
    class Meta:
        model = Shipping
        fields = [
            'id',
            'shipping_no',
            'shipping_date',
            'order',
            'order_item',
            'product_details',
            'quantity',
            'package_number',
            'shipping_note'
        ]
        read_only_fields = ['shipping_no']

    def create(self, validated_data):
        with atomic():
            order_item = validated_data['order_item']
            quantity = validated_data['quantity']
            order = validated_data['order']
            
            # Create the shipping record
            shipping = Shipping.objects.create(**validated_data)
            
            # Update the fulfilled quantity on the order item
            all_shipments = Shipping.objects.filter(order_item=order_item)
            total_shipped = all_shipments.aggregate(total=Sum('quantity'))['total'] or 0
            SalesOrderItem.objects.filter(id=order_item.id).update(fulfilled_quantity=total_shipped)
            
            order_item.refresh_from_db()
            order.refresh_from_db()
            
            # Fix the field name from 'quantity' to 'ordered_quantity'
            if all([item.fulfilled_quantity >= item.ordered_quantity for item in order.items.all()]):
                if order.status != 'CLOSED':
                    order.status = 'CLOSED'
                    order.save(update_fields=['status'])
            else:
                if order.status == 'CLOSED':
                    order.status = 'OPEN'
                    order.save(update_fields=['status'])
            
            shipping = Shipping.objects.select_related('order', 'order_item').prefetch_related('order_item__product').get(id=shipping.id)
            return shipping


class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True)
    shipments = ShippingSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id',
            'order_number',
            'customer',
            'customer_name',
            'created_at',
            'approved_by',
            'status',
            'status_display',
            'items',
            'shipments'
        ]

    def to_representation(self, instance):
        instance.refresh_from_db()
        for item in instance.items.all():
            item.refresh_from_db()
        return super().to_representation(instance)

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sales_order = SalesOrder.objects.create(**validated_data)
        for item_data in items_data:
            SalesOrderItem.objects.create(sales_order=sales_order, **item_data)
        return sales_order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                SalesOrderItem.objects.create(sales_order=instance, **item_data)
        return instance