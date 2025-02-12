from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_password_creation_email(user, request):
    """
    Send a password creation email to a newly created user.
    
    Args:
        user: The User instance who needs to set their password
        request: The HTTP request object
    """
    try:
        # Generate the password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Build the password creation URL
        domain = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        password_set_url = f"{protocol}://{domain}/set-password/{uid}/{token}/"
        
        # Prepare email content
        subject = 'Set Your Password - ERP System Access'
        message = f"""
        Hello {user.get_full_name() or user.username},

        Your account has been created in the ERP system. Please click the link below to set your password:

        {password_set_url}

        This link will expire in 24 hours for security reasons.

        If you did not request this account, please ignore this email.

        Best regards,
        ERP System Team
        """
        
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Password creation email sent successfully to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password creation email to {user.email}: {str(e)}")
        return False 