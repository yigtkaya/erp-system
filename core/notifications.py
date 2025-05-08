# core/notifications.py
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class NotificationService:
    @staticmethod
    def send_email(subject, message, recipient_list, context=None, template=None):
        """
        Generic method to send emails using Resend
        
        Args:
            subject: Email subject
            message: Email message (plain text or HTML)
            recipient_list: List of email recipients
            context: Dictionary of context for template rendering (optional)
            template: Path to template file (optional)
        """
        # If template and context are provided, render the template
        if template and context:
            message = render_to_string(template, context)
        
        with get_connection(
            host=settings.RESEND_SMTP_HOST,
            port=settings.RESEND_SMTP_PORT,
            username=settings.RESEND_SMTP_USERNAME,
            password=os.environ.get("RESEND_API_KEY", settings.EMAIL_HOST_PASSWORD),
            use_tls=True,
        ) as connection:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                connection=connection
            )
            email.content_subtype = 'html'
            return email.send()
    
    @staticmethod
    def send_low_stock_alert(product):
        subject = f"Low Stock Alert: {product.product_code}"
        recipient_list = [user.email for user in User.objects.filter(role='ADMIN')]
        
        context = {
            'product': product,
            'current_stock': product.current_stock,
            'reorder_point': product.reorder_point
        }
        
        return NotificationService.send_email(
            subject=subject,
            message='',
            recipient_list=recipient_list,
            context=context,
            template='emails/low_stock_alert.html'
        )
    
    @staticmethod
    def send_order_confirmation(order):
        subject = f"Order Confirmation: {order.order_number}"
        recipient_list = [order.customer.email]
        
        context = {
            'order': order
        }
        
        return NotificationService.send_email(
            subject=subject,
            message='',
            recipient_list=recipient_list,
            context=context,
            template='emails/order_confirmation.html'
        )