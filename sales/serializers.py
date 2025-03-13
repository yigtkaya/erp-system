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
    order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    order_id = serializers.CharField(source='sales_order.id', read_only=True)
    product_details = ProductSerializer(source='product', read_only=True)
    receiving_date = DateTimeToDateField(required=False, allow_null=True)
    deadline_date = DateTimeToDateField(required=False, allow_null=True)
    kapsam_deadline_date = DateTimeToDateField(required=False, allow_null=True)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        required=True
    )
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'id',
            'order_id',
            'order_number',
            'product',
            'product_details',
            'ordered_quantity',
            'fulfilled_quantity',
            'receiving_date',
            'deadline_date',
            'kapsam_deadline_date'
        ]
        read_only_fields = ['fulfilled_quantity']
        extra_kwargs = {
            'product': {'required': True}
        }

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


class BatchSalesOrderItemUpdateSerializer(serializers.Serializer):
    """
    Serializer for batch updating multiple SalesOrderItems in a single request.
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        required=True
    )
    
    def validate_items(self, items):
        """
        Validate that each item in the list has an id and belongs to the same order.
        """
        if not items:
            raise serializers.ValidationError("At least one item must be provided")
        
        # Check that all items have an id
        for i, item in enumerate(items):
            if 'id' not in item:
                raise serializers.ValidationError(f"Item at position {i} is missing an 'id' field")
        
        # Get the order_id from the context
        order_id = self.context.get('order_id')
        if not order_id:
            raise serializers.ValidationError("Order ID is required in context")
            
        # Verify all items exist and belong to the specified order
        item_ids = [item['id'] for item in items]
        existing_items = SalesOrderItem.objects.filter(id__in=item_ids, sales_order_id=order_id)
        
        if len(existing_items) != len(item_ids):
            found_ids = set(existing_items.values_list('id', flat=True))
            missing_ids = set(item_ids) - found_ids
            raise serializers.ValidationError(f"Items with IDs {missing_ids} do not exist or do not belong to this order")
            
        return items
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update multiple SalesOrderItems.
        The 'instance' parameter is the SalesOrder object.
        """
        items_data = validated_data.get('items', [])
        updated_items = []
        errors = {}
        
        for item_data in items_data:
            item_id = item_data.pop('id')
            try:
                item = SalesOrderItem.objects.get(id=item_id, sales_order=instance)
                
                # Use the individual item serializer for validation
                item_serializer = SalesOrderItemSerializer(
                    item, 
                    data=item_data, 
                    partial=True,
                    context=self.context
                )
                
                if item_serializer.is_valid():
                    updated_item = item_serializer.save()
                    updated_items.append(updated_item)
                else:
                    errors[item_id] = item_serializer.errors
            except SalesOrderItem.DoesNotExist:
                errors[item_id] = {"detail": "Item does not exist or does not belong to this order"}
        
        if errors:
            raise serializers.ValidationError(errors)
            
        # Update order status after all items are updated
        instance.update_order_status()
        
        return {
            'order': instance,
            'updated_items': updated_items
        }


class BatchSalesOrderItemCreateSerializer(serializers.Serializer):
    """
    Serializer for bulk creating multiple SalesOrderItems in a single request.
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        required=True
    )
    
    def validate_items(self, items):
        """
        Validate that each item in the list has required fields.
        """
        if not items:
            raise serializers.ValidationError("At least one item must be provided")
        
        # Check that all items have required fields
        for i, item in enumerate(items):
            if 'product' not in item:
                raise serializers.ValidationError(f"Item at position {i} is missing a 'product' field")
            if 'ordered_quantity' not in item:
                raise serializers.ValidationError(f"Item at position {i} is missing an 'ordered_quantity' field")
        
        # Get the order_id from the context
        order_id = self.context.get('order_id')
        if not order_id:
            raise serializers.ValidationError("Order ID is required in context")
            
        return items
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Create multiple SalesOrderItems.
        """
        items_data = validated_data.get('items', [])
        order_id = self.context.get('order_id')
        order = SalesOrder.objects.get(id=order_id)
        
        created_items = []
        errors = {}
        
        for i, item_data in enumerate(items_data):
            try:
                # Use the individual item serializer for validation
                item_serializer = SalesOrderItemSerializer(
                    data=item_data,
                    context=self.context
                )
                
                if item_serializer.is_valid():
                    # Create the item with the sales_order reference
                    item = SalesOrderItem(sales_order=order, **item_serializer.validated_data)
                    item.full_clean()  # Run model validation
                    item.save()
                    created_items.append(item)
                else:
                    errors[i] = item_serializer.errors
            except Exception as e:
                errors[i] = {"detail": str(e)}
        
        if errors:
            raise serializers.ValidationError(errors)
            
        # Update order status after all items are created
        order.update_order_status()
        
        return {
            'order': order,
            'created_items': created_items
        }


class ShippingSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='order_item.product', read_only=True)
    
    class Meta:
        model = Shipping
        fields = [
            'id', 'shipping_no', 'shipping_date',
            'order', 'order_item', 'product_details',
            'quantity', 'package_number', 'shipping_note'
        ]

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

    def to_internal_value(self, data):
        # Handle cases where items array is sent as top-level data
        if isinstance(data, list):
            return super().to_internal_value({'items': data})
        return super().to_internal_value(data)

    def validate(self, data):
        # Only validate items during creation, not updates
        if self.instance is None:  # Creation case
            items = data.get('items', [])
            if len(items) == 0:
                raise ValidationError("Order must contain at least one item")
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        sales_order = SalesOrder.objects.create(**validated_data)
        for item_data in items_data:
            if 'product' not in item_data:
                raise serializers.ValidationError("Product is required for all items")
            SalesOrderItem.objects.create(sales_order=sales_order, **item_data)
        return sales_order

    def update(self, instance, validated_data):
        # Change from pop() to get() to maintain existing items if not provided
        items_data = validated_data.get('items')
        
        # Update order fields
        for attr, value in validated_data.items():
            if attr != 'items':  # Skip items field here
                setattr(instance, attr, value)
        instance.save()

        # Only update items if they're provided in the request
        if items_data is not None:
            self.update_items(instance, items_data)

        return instance

    def update_items(self, instance, items_data):
        """Helper method to update multiple order items"""
        with transaction.atomic():
            existing_items = {item.id: item for item in instance.items.all()}
            updated_ids = []
            
            # Update or create items
            for item_data in items_data:
                item_id = item_data.get('id')
                
                if item_id and item_id in existing_items:
                    # Update existing item
                    item = existing_items[item_id]
                    for key, value in item_data.items():
                        setattr(item, key, value)
                    item.full_clean()
                    item.save()
                    updated_ids.append(item_id)
                else:
                    # Create new item
                    SalesOrderItem.objects.create(sales_order=instance, **item_data)
            
            # Delete items not included in the update
            to_delete_ids = set(existing_items.keys()) - set(updated_ids)
            if to_delete_ids:
                SalesOrderItem.objects.filter(id__in=to_delete_ids).delete()
            
            # Refresh instance and update status
            instance.refresh_from_db()
            instance.update_order_status()


class BatchShippingUpdateSerializer(serializers.Serializer):
    """
    Serializer for batch updating multiple Shipping records
    """
    items = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        required=True
    )

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one shipping record must be provided")
        
        for i, item in enumerate(items):
            if 'id' not in item:
                raise serializers.ValidationError(f"Item at position {i} is missing 'id' field")
            if 'shipping_no' not in item:
                raise serializers.ValidationError(f"Item at position {i} is missing 'shipping_no' field")
        
        return items

    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.get('items', [])
        updated_shipments = []
        errors = {}

        for item_data in items_data:
            try:
                shipment = Shipping.objects.get(
                    shipping_no=item_data['shipping_no'],
                    id=item_data['id']
                )
                
                serializer = ShippingSerializer(
                    shipment,
                    data=item_data,
                    partial=True,
                    context=self.context
                )
                
                if serializer.is_valid():
                    updated_shipment = serializer.save()
                    updated_shipments.append(updated_shipment)
                else:
                    errors[item_data['shipping_no']] = serializer.errors
            except Shipping.DoesNotExist:
                errors[item_data['shipping_no']] = "Shipping not found"
        
        if errors:
            raise serializers.ValidationError(errors)
            
        return {'updated_shipments': updated_shipments}


class BatchOrderShipmentUpdateSerializer(serializers.Serializer):
    """
    Serializer for batch updating multiple Shipping records within a sale order
    """
    shipments = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(required=False),
            allow_empty=False
        ),
        required=True,
        allow_empty=False
    )

    def validate_shipments(self, shipments):
        validated_shipments = []
        for item in shipments:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Each shipment must be a dictionary")
            
            if 'shipping_no' not in item:
                raise serializers.ValidationError("shipping_no is required for each shipment")

            # Validate required fields
            required_fields = {'shipping_no', 'quantity', 'shipping_date'}
            missing_fields = required_fields - set(item.keys())
            if missing_fields:
                raise serializers.ValidationError(f"Missing required fields: {missing_fields}")

            # Validate shipping exists and belongs to the order
            try:
                shipping = Shipping.objects.get(shipping_no=item['shipping_no'])
                if shipping.order.id != self.context['order_id']:
                    raise serializers.ValidationError(
                        f"Shipping {item['shipping_no']} does not belong to this order"
                    )
            except Shipping.DoesNotExist:
                raise serializers.ValidationError(
                    f"Shipping with number {item['shipping_no']} not found"
                )

            # Validate quantity
            try:
                quantity = int(item['quantity'])
                if quantity <= 0:
                    raise serializers.ValidationError("Quantity must be positive")
            except (ValueError, TypeError):
                raise serializers.ValidationError("Quantity must be a valid integer")

            # Validate shipping date
            try:
                shipping_date = parse(item['shipping_date']).date()
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    "shipping_date must be a valid date in YYYY-MM-DD format"
                )

            validated_shipments.append({
                'shipping': shipping,
                'quantity': quantity,
                'shipping_date': shipping_date,
                'shipping_note': item.get('shipping_note', '')
            })

        return validated_shipments

    @transaction.atomic
    def update(self, instance, validated_data):
        updated_shipments = []
        for shipment_data in validated_data['shipments']:
            shipping = shipment_data['shipping']
            
            # Update shipping
            shipping.quantity = shipment_data['quantity']
            shipping.shipping_date = shipment_data['shipping_date']
            if shipment_data.get('shipping_note'):
                shipping.shipping_note = shipment_data['shipping_note']
            
            shipping.save()
            
            # Update order item's fulfilled quantity
            shipping.order_item.update_fulfilled_quantity()
            shipping.order_item.save()
            
            # Update order status
            shipping.order.update_order_status()
            
            updated_shipments.append(shipping)

        return updated_shipments