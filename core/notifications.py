# core/notifications.py
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

class NotificationService:
    @staticmethod
    def send_low_stock_alert(product):
        subject = f"Low Stock Alert: {product.product_code}"
        message = render_to_string('emails/low_stock_alert.html', {
            'product': product,
            'current_stock': product.current_stock,
            'reorder_point': product.reorder_point
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email for user in User.objects.filter(role='ADMIN')],
            html_message=message
        )
    
    @staticmethod
    def send_order_confirmation(order):
        subject = f"Order Confirmation: {order.order_number}"
        message = render_to_string('emails/order_confirmation.html', {
            'order': order
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            html_message=message
        )