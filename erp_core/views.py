from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from inventory.models import Product, RawMaterial, InventoryTransaction
from manufacturing.models import WorkOrder, Machine
from sales.models import SalesOrder
from django.utils import timezone
from datetime import timedelta

@login_required
def home(request):
    """
    Main dashboard view for the ERP system with database statistics
    """
    # Get current date for filtering
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)

    # Inventory Statistics
    inventory_stats = {
        'total_products': Product.objects.count(),
        'total_raw_materials': RawMaterial.objects.count(),
        'recent_transactions': InventoryTransaction.objects.filter(
            created_at__gte=thirty_days_ago
        ).count(),
        'low_stock_products': Product.objects.filter(quantity__lte=10).count(),
    }

    # Manufacturing Statistics
    manufacturing_stats = {
        'total_work_orders': WorkOrder.objects.count(),
        'active_work_orders': WorkOrder.objects.filter(status='IN_PROGRESS').count(),
        'completed_work_orders': WorkOrder.objects.filter(
            status='COMPLETED',
            completed_at__gte=thirty_days_ago
        ).count(),
        'total_machines': Machine.objects.count(),
    }

    # Sales Statistics
    sales_stats = {
        'total_orders': SalesOrder.objects.count(),
        'recent_orders': SalesOrder.objects.filter(
            created_at__gte=thirty_days_ago
        ).count(),
        'pending_orders': SalesOrder.objects.filter(status='PENDING').count(),
        'completed_orders': SalesOrder.objects.filter(status='COMPLETED').count(),
    }

    context = {
        'title': 'ERP System Dashboard',
        'inventory_stats': inventory_stats,
        'manufacturing_stats': manufacturing_stats,
        'sales_stats': sales_stats,
    }
    return render(request, 'erp_core/home.html', context) 