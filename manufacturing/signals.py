from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WorkOrderOutput
from inventory.models import InventoryTransaction

@receiver(post_save, sender=WorkOrderOutput)
def update_inventory_on_output(sender, instance, created, **kwargs):
    if created:
        # Create inventory transaction based on output status
        transaction_type = {
            'GOOD': 'PRODUCTION',
            'REWORK': 'ADJUSTMENT',
            'SCRAP': 'SCRAP'
        }.get(instance.status, 'ADJUSTMENT')

        InventoryTransaction.objects.create(
            product=instance.sub_work_order.bom_component.semi_product,
            material=instance.sub_work_order.bom_component.raw_material,
            quantity_change=instance.quantity if instance.status == 'GOOD' else -instance.quantity,
            transaction_type=transaction_type,
            performed_by=instance.sub_work_order.parent_work_order.created_by,
            notes=f"Work order output: {instance.sub_work_order.parent_work_order.order_number}",
            to_category=instance.target_category
        ) 