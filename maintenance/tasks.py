from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import MaintenancePlan, MaintenanceWorkOrder, Equipment
from core.emails import EmailService
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_maintenance_due():
    """Check for due maintenance and create work orders"""
    today = timezone.now().date()
    
    # Get maintenance plans that are due
    due_plans = MaintenancePlan.objects.filter(
        is_active=True,
        next_due_date__lte=today
    )
    
    for plan in due_plans:
        # Create work order
        work_order = MaintenanceWorkOrder.objects.create(
            equipment=plan.equipment,
            maintenance_plan=plan,
            maintenance_type=plan.maintenance_type,
            priority='MEDIUM',
            status='SCHEDULED',
            description=f"Scheduled maintenance: {plan.plan_name}",
            scheduled_start=timezone.now() + timedelta(days=1),
            scheduled_end=timezone.now() + timedelta(days=1, hours=int(plan.estimated_duration_hours)),
            estimated_hours=plan.estimated_duration_hours,
            created_by_id=1  # System user
        )
        
        # Update next due date
        plan.next_due_date = plan.next_due_date + timedelta(days=plan.frequency_days)
        plan.save()
        
        # Send notification
        notify_maintenance_due.delay(work_order.id)
    
    logger.info(f"Created {due_plans.count()} maintenance work orders")
    return due_plans.count()

@shared_task
def notify_maintenance_due(work_order_id):
    """Send maintenance due notification"""
    try:
        work_order = MaintenanceWorkOrder.objects.get(id=work_order_id)
        
        # Assign to default maintenance technician
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Find a user with maintenance role or use first engineer
        technician = User.objects.filter(
            role='ENGINEER',
            department_memberships__department__name='Maintenance'
        ).first()
        
        if not technician:
            technician = User.objects.filter(role='ENGINEER').first()
        
        if technician:
            work_order.assigned_to = technician
            work_order.save()
            
            # Send email
            EmailService.send_maintenance_reminder(work_order)
    except MaintenanceWorkOrder.DoesNotExist:
        logger.error(f"Work order {work_order_id} not found")

@shared_task
def check_overdue_maintenance():
    """Check for overdue maintenance work orders"""
    overdue_orders = MaintenanceWorkOrder.objects.filter(
        status__in=['SCHEDULED', 'IN_PROGRESS'],
        scheduled_end__lt=timezone.now()
    )
    
    for order in overdue_orders:
        # Update status
        order.status = 'OVERDUE'
        order.save()
        
        # Send notification
        if order.assigned_to:
            context = {
                'work_order': order,
                'overdue_days': (timezone.now() - order.scheduled_end).days,
            }
            
            EmailService.send_email(
                subject=f'Overdue Maintenance: {order.work_order_number}',
                template_name='emails/maintenance_overdue.html',
                context=context,
                to_emails=order.assigned_to.email
            )
    
    return overdue_orders.count()

@shared_task
def calculate_equipment_uptime():
    """Calculate equipment uptime statistics"""
    # Note: Equipment uptime calculation should be based on maintenance records
    # not machine downtime records, as these are separate concerns
    
    equipment_list = Equipment.objects.filter(status='ACTIVE')
    stats = {}
    
    for equipment in equipment_list:
        # Calculate uptime based on maintenance downtime for last 30 days
        start_date = timezone.now() - timedelta(days=30)
        
        # Get maintenance work orders that caused downtime
        maintenance_downtimes = MaintenanceWorkOrder.objects.filter(
            equipment=equipment,
            actual_start_date__gte=start_date,
            status='COMPLETED'
        )
        
        total_downtime_hours = 0
        for wo in maintenance_downtimes:
            if wo.total_downtime_hours:
                total_downtime_hours += float(wo.total_downtime_hours)
        
        # Assuming 24/7 operation
        total_hours = 30 * 24
        uptime_percentage = ((total_hours - total_downtime_hours) / total_hours) * 100
        
        stats[equipment.code] = {
            'uptime_percentage': round(uptime_percentage, 2),
            'downtime_hours': round(total_downtime_hours, 2)
        }
    
    logger.info(f"Calculated uptime for {len(stats)} equipment")
    return stats