from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import SalesOrder, SalesOrderItem, SalesQuotation
from core.emails import EmailService
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_overdue_orders():
    """Process overdue sales order items"""
    overdue_items = SalesOrderItem.objects.filter(
        sales_order__status__in=['CONFIRMED', 'IN_PRODUCTION'],
        delivery_date__lt=timezone.now().date()
    ).select_related('sales_order', 'product')
    
    # Group by sales order to avoid duplicate notifications
    processed_orders = set()
    
    for item in overdue_items:
        if item.sales_order.id not in processed_orders:
            notify_overdue_order.delay(item.sales_order.id)
            processed_orders.add(item.sales_order.id)
    
    logger.info(f"Processed {len(processed_orders)} orders with overdue items")
    return len(processed_orders)

@shared_task
def process_overdue_kapsam_deadlines():
    """Process overdue kapsam deadline items"""
    overdue_kapsam_items = SalesOrderItem.objects.filter(
        sales_order__status__in=['CONFIRMED', 'IN_PRODUCTION'],
        kapsam_deadline_date__lt=timezone.now().date()
    ).select_related('sales_order', 'product')
    
    # Group by sales order to avoid duplicate notifications
    processed_orders = set()
    
    for item in overdue_kapsam_items:
        if item.sales_order.id not in processed_orders:
            notify_overdue_kapsam.delay(item.sales_order.id)
            processed_orders.add(item.sales_order.id)
    
    logger.info(f"Processed {len(processed_orders)} orders with overdue kapsam deadlines")
    return len(processed_orders)

@shared_task
def notify_overdue_order(order_id):
    """Send notification for overdue order items"""
    try:
        order = SalesOrder.objects.get(id=order_id)
        overdue_items = order.items.filter(
            delivery_date__lt=timezone.now().date()
        )
        
        if not overdue_items.exists():
            return
        
        context = {
            'order': order,
            'overdue_items': overdue_items,
            'max_delay_days': max((timezone.now().date() - item.delivery_date).days for item in overdue_items),
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
def notify_overdue_kapsam(order_id):
    """Send notification for overdue kapsam deadline items"""
    try:
        order = SalesOrder.objects.get(id=order_id)
        overdue_kapsam_items = order.items.filter(
            kapsam_deadline_date__lt=timezone.now().date()
        )
        
        if not overdue_kapsam_items.exists():
            return
        
        context = {
            'order': order,
            'overdue_kapsam_items': overdue_kapsam_items,
            'max_delay_days': max((timezone.now().date() - item.kapsam_deadline_date).days for item in overdue_kapsam_items),
        }
        
        EmailService.send_email(
            subject=f'Order {order.order_number} - Kapsam Deadline Alert',
            template_name='emails/order_kapsam_overdue.html',
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