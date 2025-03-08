from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import SalesOrder, Shipping
from inventory.models import InventoryTransaction
from django.core.exceptions import ValidationError

@receiver(post_save, sender=Shipping)
def handle_shipment_inventory(sender, instance, created, **kwargs):
    """Handle actual inventory deduction when shipping is created"""
    if created and instance.order_item:
        with transaction.atomic():
            product = instance.order_item.product
            quantity = instance.quantity
            
            # Create actual OUT transaction
            InventoryTransaction.objects.create(
                product=product,
                quantity_change=-quantity,
                transaction_type='OUT',
                reference_id=f"SHIP-{instance.shipping_no}",
                notes=f"Order shipment {instance.shipping_no}",
                performed_by=instance.created_by
            )

@receiver(pre_delete, sender=SalesOrder)
def handle_sales_order_deletion(sender, instance, **kwargs):
    """Clean up shipment transactions when order is deleted"""
    with transaction.atomic():
        # Delete all related inventory transactions for shipments
        shipment_ids = [str(id) for id in instance.shipments.values_list('id', flat=True)]
        if shipment_ids:
            InventoryTransaction.objects.filter(
                reference_id__in=shipment_ids,
                transaction_type='OUT'
            ).delete() 

@receiver(pre_delete, sender=Shipping)
def handle_shipment_deletion(sender, instance, **kwargs):
    """Clean up inventory transactions when shipment is deleted"""
    with transaction.atomic():
        # Delete related OUT transaction
        InventoryTransaction.objects.filter(
            reference_id=f"SHIP-{instance.shipping_no}",
            transaction_type='OUT'
        ).delete()
        
        # Update fulfilled quantity
        instance.order_item.update_fulfilled_quantity() 