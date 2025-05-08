from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_email(subject, template_name, context, to_emails, attachments=None):
        """Send email using template"""
        try:
            # Add common context
            context['frontend_url'] = settings.FRONTEND_URL
            context['current_year'] = timezone.now().year
            
            html_message = render_to_string(template_name, context)
            plain_message = strip_tags(html_message)
            
            email = EmailMessage(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=to_emails if isinstance(to_emails, list) else [to_emails],
            )
            email.content_subtype = 'html'
            email.body = html_message
            
            if attachments:
                for filename, content, mimetype in attachments:
                    email.attach(filename, content, mimetype)
            
            email.send()
            logger.info(f"Email sent to {to_emails}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    @staticmethod
    def send_user_welcome_email(user):
        """Send welcome email to new user"""
        context = {
            'user': user,
            'login_url': settings.FRONTEND_URL + '/login',
        }
        return EmailService.send_email(
            subject='Welcome to ERP System',
            template_name='emails/welcome.html',
            context=context,
            to_emails=user.email
        )
    
    @staticmethod
    def send_order_confirmation(order):
        """Send order confirmation email"""
        context = {
            'order': order,
            'order_url': f"{settings.FRONTEND_URL}/orders/{order.id}",
        }
        return EmailService.send_email(
            subject=f'Order Confirmation - {order.order_number}',
            template_name='emails/order_confirmation.html',
            context=context,
            to_emails=order.customer.email
        )
    
    @staticmethod
    def send_low_stock_alert(product):
        """Send low stock alert to admins"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        admins = User.objects.filter(role='ADMIN', is_active=True)
        admin_emails = list(admins.values_list('email', flat=True))
        
        context = {
            'product': product,
            'current_stock': product.current_stock,
            'reorder_point': product.reorder_point,
            'product_url': f"{settings.FRONTEND_URL}/products/{product.id}",
        }
        
        return EmailService.send_email(
            subject=f'Low Stock Alert - {product.product_code}',
            template_name='emails/low_stock_alert.html',
            context=context,
            to_emails=admin_emails
        )
    
    @staticmethod
    def send_maintenance_reminder(work_order):
        """Send maintenance reminder"""
        context = {
            'work_order': work_order,
            'equipment': work_order.equipment,
            'scheduled_date': work_order.scheduled_start,
            'work_order_url': f"{settings.FRONTEND_URL}/maintenance/{work_order.id}",
        }
        
        return EmailService.send_email(
            subject=f'Maintenance Reminder - {work_order.equipment.name}',
            template_name='emails/maintenance_reminder.html',
            context=context,
            to_emails=work_order.assigned_to.email
        )
    
    @staticmethod
    def send_quality_alert(nonconformance):
        """Send quality nonconformance alert"""
        context = {
            'nonconformance': nonconformance,
            'product': nonconformance.product,
            'nc_url': f"{settings.FRONTEND_URL}/quality/nc/{nonconformance.id}",
        }
        
        return EmailService.send_email(
            subject=f'Quality Alert - NC {nonconformance.nc_number}',
            template_name='emails/quality_alert.html',
            context=context,
            to_emails=[nonconformance.assigned_to.email, nonconformance.reported_by.email]
        )