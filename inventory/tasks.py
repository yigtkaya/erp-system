from celery import shared_task
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from .models import Product
from purchasing.models import PurchaseRequisition, PurchaseRequisitionItem
from core.emails import EmailService
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_low_stock():
    """Check for products below reorder point"""
    low_stock_products = Product.objects.filter(
        is_active=True,
        current_stock__lte=F('reorder_point')
    )
    
    for product in low_stock_products:
        # Send email notification
        EmailService.send_low_stock_alert(product)
        
        # Create purchase requisition if needed
        create_purchase_requisition.delay(product.id)
    
    logger.info(f"Checked {low_stock_products.count()} products with low stock")
    return low_stock_products.count()

@shared_task
def create_purchase_requisition(product_id):
    """Create purchase requisition for low stock product"""
    try:
        product = Product.objects.get(id=product_id)
        
        # Check if requisition already exists
        existing = PurchaseRequisitionItem.objects.filter(
            product=product,
            requisition__status__in=['DRAFT', 'SUBMITTED', 'APPROVED']
        ).exists()
        
        if not existing:
            # Get system user (user with ID=1 or create one)
            from django.contrib.auth import get_user_model
            User = get_user_model()
            system_user = User.objects.filter(username='system').first()
            if not system_user:
                system_user = User.objects.first()  # Fallback to first user
            
            # Create requisition
            requisition = PurchaseRequisition.objects.create(
                requested_by=system_user,
                required_date=timezone.now().date() + timedelta(days=7),
                department_id=1,  # Default department
                notes=f"Auto-generated for low stock: {product.product_code}",
                status='SUBMITTED'
            )
            
            # Calculate order quantity (2x reorder point or minimum 10)
            order_quantity = max(product.reorder_point * 2, 10) if product.reorder_point else 10
            
            # Add item
            PurchaseRequisitionItem.objects.create(
                requisition=requisition,
                product=product,
                quantity=order_quantity,
                notes="Auto-generated due to low stock"
            )
            
            logger.info(f"Created purchase requisition for {product.product_code}")
    except Product.DoesNotExist:
        logger.error(f"Product {product_id} not found")
    except Exception as e:
        logger.error(f"Error creating purchase requisition: {str(e)}")

@shared_task
def update_inventory_valuations():
    """Update inventory valuations"""
    products = Product.objects.filter(is_active=True)
    total_value = 0
    
    for product in products:
        if hasattr(product, 'unit_cost') and product.unit_cost:
            value = product.current_stock * product.unit_cost
            total_value += value
    
    logger.info(f"Total inventory value: {total_value}")
    return total_value