from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import SalesOrderItem, SalesOrder, Shipping
from inventory.models import InventoryTransaction, Product
from django.core.exceptions import ValidationError

@receiver(post_save, sender=SalesOrderItem)
def handle_inventory_reservation(sender, instance, created, **kwargs):
    # Skip reservation check if this update is from a shipment process
    # We can detect this by checking if the update is only for fulfilled_quantity
    if hasattr(instance, '_update_from_shipment') and instance._update_from_shipment:
        return
        
    with transaction.atomic():
        # Lock the product row
        product = Product.objects.select_for_update().get(pk=instance.product.id)
        
        # Calculate quantity difference
        old_quantity = instance._old_quantity if hasattr(instance, '_old_quantity') else 0
        delta = instance.quantity - old_quantity
        
        if instance.sales_order.status == 'OPEN':
            if product.current_stock >= delta:
                product.current_stock = F('current_stock') - delta
                product.save(update_fields=['current_stock'])
                
                InventoryTransaction.objects.update_or_create(
                    reference_id=instance.id,
                    transaction_type='RESERVATION',
                    defaults={
                        'product': product,
                        'quantity_change': -delta,
                        'notes': f"Sales order {instance.sales_order.order_number}",
                        'performed_by': instance.sales_order.created_by
                    }
                )
            else:
                raise ValidationError("Insufficient stock for reservation")

@receiver(pre_delete, sender=SalesOrderItem)
def release_inventory_on_delete(sender, instance, **kwargs):
    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=instance.product.id)
        product.current_stock = F('current_stock') + instance.quantity
        product.save(update_fields=['current_stock'])
        
        # Convert ID to string for consistency
        InventoryTransaction.objects.filter(
            reference_id=str(instance.id),
            transaction_type='RESERVATION'
        ).delete()

# Add signal for order status changes
@receiver(post_save, sender=SalesOrder)
def handle_order_approval(sender, instance, **kwargs):
    if instance.tracker.has_changed('status'):
        with transaction.atomic():
            if instance.status == 'APPROVED':
                for item in instance.items.all():
                    handle_inventory_reservation(SalesOrderItem, item, False)
            elif instance.status in ['CANCELLED', 'REJECTED']:
                for item in instance.items.all():
                    release_inventory_on_delete(SalesOrderItem, item)

@receiver(pre_delete, sender=SalesOrder)
def handle_sales_order_deletion(sender, instance, **kwargs):
    """Handle cleanup when a sales order is deleted"""
    with transaction.atomic():
        # Delete all related inventory transactions for shipments
        # Convert UUID to string for shipment reference IDs
        shipment_ids = [str(id) for id in instance.shipments.values_list('id', flat=True)]
        if shipment_ids:
            InventoryTransaction.objects.filter(
                reference_id__in=shipment_ids,
                transaction_type='SHIPMENT'
            ).delete()
        
        # Delete all reservation transactions for order items
        # Order item IDs are already integers
        order_item_ids = list(instance.items.values_list('id', flat=True))
        if order_item_ids:
            InventoryTransaction.objects.filter(
                reference_id__in=[str(id) for id in order_item_ids],
                transaction_type='RESERVATION'
            ).delete()
        
        # Return reserved quantities back to stock
        for item in instance.items.all():
            if item.quantity > 0:  # Only update stock if there was a reservation
                product = Product.objects.select_for_update().get(pk=item.product.id)
                product.current_stock = F('current_stock') + item.quantity
                product.save(update_fields=['current_stock']) 