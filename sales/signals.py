from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import SalesOrderItem, SalesOrder
from inventory.models import InventoryTransaction, Product
from django.core.exceptions import ValidationError

@receiver(post_save, sender=SalesOrderItem)
def handle_inventory_reservation(sender, instance, created, **kwargs):
    with transaction.atomic():
        # Lock the product row
        product = Product.objects.select_for_update().get(pk=instance.product.id)
        
        # Calculate quantity difference
        old_quantity = instance._old_quantity if hasattr(instance, '_old_quantity') else 0
        delta = instance.quantity - old_quantity
        
        if instance.sales_order.status == 'APPROVED':
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
        
        InventoryTransaction.objects.filter(
            reference_id=instance.id,
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