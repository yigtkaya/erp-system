from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import PurchaseOrderItem
from inventory.models import InventoryTransaction

@receiver(post_save, sender=PurchaseOrderItem)
def update_inventory_on_receipt(sender, instance, **kwargs):
    if instance.tracker.has_changed('received_quantity'):
        try:
            with transaction.atomic():
                delta = instance.received_quantity - (instance.tracker.previous('received_quantity') or 0)
                if delta > 0:
                    InventoryTransaction.objects.create(
                        product=instance.product,
                        quantity_change=delta,
                        transaction_type='IN',
                        performed_by=instance.modified_by,
                        notes=f"Purchase order {instance.purchase_order.order_number}"
                    )
        except Exception as e:
            # Log the error here if you have logging configured
            raise Exception(f"Failed to create inventory transaction: {str(e)}") 