from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import WorkOrderOutput, Machine, WorkOrder, SubWorkOrderProcess, WorkOrderStatusChange
from inventory.models import InventoryTransaction

@receiver(post_save, sender=WorkOrderOutput)
def update_inventory_on_output(sender, instance, created, **kwargs):
    if created:
        # Get the component instance
        component = instance.sub_work_order.bom_component
        
        # Create inventory transaction based on output status
        transaction_type = {
            'GOOD': 'PRODUCTION',
            'REWORK': 'ADJUSTMENT',
            'SCRAP': 'SCRAP'
        }.get(instance.status, 'ADJUSTMENT')

        # For raw material components, use the raw material
        # For product components, use the product
        product = None
        material = None
        if component.component_type == 'RAW_MATERIAL':
            material = component.raw_material
        else:  # PRODUCT
            product = component.product

        InventoryTransaction.objects.create(
            product=product,
            material=material,
            quantity_change=instance.quantity if instance.status == 'GOOD' else -instance.quantity,
            transaction_type=transaction_type,
            performed_by=instance.sub_work_order.parent_work_order.created_by,
            notes=f"Work order output: {instance.sub_work_order.parent_work_order.order_number}",
            to_category=instance.target_category
        ) 

@receiver(pre_save, sender=Machine)
def update_maintenance_schedule(sender, instance, **kwargs):
    """Update next maintenance date when last maintenance date changes."""
    if instance.pk:  # Only for existing machines
        old_instance = Machine.objects.get(pk=instance.pk)
        if instance.last_maintenance_date != old_instance.last_maintenance_date:
            if instance.last_maintenance_date and instance.maintenance_interval:
                instance.next_maintenance_date = instance.last_maintenance_date + timezone.timedelta(days=instance.maintenance_interval)

@receiver(post_save, sender=WorkOrder)
def create_work_order_status_change(sender, instance, created, **kwargs):
    """Create status change record when work order status changes."""
    if not created:
        try:
            old_instance = WorkOrder.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                WorkOrderStatusChange.objects.create(
                    work_order=instance,
                    from_status=old_instance.status,
                    to_status=instance.status,
                    changed_by=instance.modified_by,
                    notes=f"Status changed from {old_instance.status} to {instance.status}"
                )
        except WorkOrder.DoesNotExist:
            pass

@receiver(post_save, sender=SubWorkOrderProcess)
def update_work_order_completion(sender, instance, **kwargs):
    """Update work order completion percentage when process status changes."""
    if instance.status == 'COMPLETED':
        sub_work_order = instance.sub_work_order
        
        # Calculate completion percentage based on completed processes
        total_processes = sub_work_order.processes.count()
        completed_processes = sub_work_order.processes.filter(status='COMPLETED').count()
        
        if total_processes > 0:
            completion_percentage = (completed_processes / total_processes) * 100
            sub_work_order.completion_percentage = completion_percentage
            sub_work_order.save()
            
            # Update parent work order completion
            parent_work_order = sub_work_order.parent_work_order
            total_sub_orders = parent_work_order.sub_orders.count()
            completed_sub_orders = parent_work_order.sub_orders.filter(status='COMPLETED').count()
            
            if total_sub_orders > 0:
                parent_completion = (completed_sub_orders / total_sub_orders) * 100
                parent_work_order.completion_percentage = parent_completion
                parent_work_order.save()