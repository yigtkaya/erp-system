from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import SalesOrder, SalesQuotation
from core.emails import EmailService
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_overdue_orders():
    """Process overdue sales orders"""
    overdue_orders = SalesOrder.objects.filter(
        status__in=['CONFIRMED', 'IN_PRODUCTION'],
        delivery_date__lt=timezone.now().date()
    )
    
    for order in overdue_orders:
        # Send notification
        notify_overdue_order.delay(order.id)
    
    logger.info(f"Processed {overdue_orders.count()} overdue orders")
    return overdue_orders.count()

@shared_task
def notify_overdue_order(order_id):
    """Send notification for overdue order"""
    try:
        order = SalesOrder.objects.get(id=order_id)
        
        # Email customer and salesperson
        context = {
            'order': order,
            'delay_days': (timezone.now().date() - order.delivery_date).days,
            'order_url': f"{settings.FRONTEND_URL}/orders/{order.id}",
        }
        
        EmailService.send_email(
            subject=f'Order {order.order_number} - Delivery Update',
            template_name='emails/order_overdue.html',
            context=context,
            to_emails=[order.customer.email, order.salesperson.email]
        )
    except SalesOrder.DoesNotExist:
        logger.error(f"Order {order_id} not found")

@shared_task
def check_expired_quotations():
    """Check for expired quotations"""
    expired_quotations = SalesQuotation.objects.filter(
        status='SENT',
        valid_until__lt=timezone.now().date()
    )
    
    for quotation in expired_quotations:
        quotation.status = 'EXPIRED'
        quotation.save()
    
    logger.info(f"Marked {expired_quotations.count()} quotations as expired")
    return expired_quotations.count()

@shared_task
def send_order_reminders():
    """Send reminders for pending orders"""
    pending_orders = SalesOrder.objects.filter(
        status='DRAFT',
        created_at__lte=timezone.now() - timedelta(days=7)
    )
    
    for order in pending_orders:
        context = {
            'order': order,
            'days_pending': (timezone.now() - order.created_at).days,
        }
        
        EmailService.send_email(
            subject=f'Reminder: Pending Order {order.order_number}',
            template_name='emails/order_reminder.html',
            context=context,
            to_emails=order.salesperson.email
        )
    
    return pending_orders.count()