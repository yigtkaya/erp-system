from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from erp_core.models import User, Department
from inventory.models import Product, RawMaterial
from sales.models import SalesOrder
from manufacturing.models import WorkOrder
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.db import connection
from django.utils import timezone
import django

@login_required
def home(request):
    context = {
        'total_users': User.objects.count(),
        'total_departments': Department.objects.count(),
        'total_products': Product.objects.count(),
        'total_raw_materials': RawMaterial.objects.count(),
        'total_sales_orders': SalesOrder.objects.count(),
        'total_work_orders': WorkOrder.objects.count(),
        'departments': Department.objects.annotate(user_count=Count('users')),
    }
    return render(request, 'erp_core/home.html', context)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """System health check endpoint"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = 'connected'
    except Exception:
        db_status = 'disconnected'

    return JsonResponse({
        'status': 'Alive and connected',
        'database': db_status,
        'django_version': django.get_version(),
        'timestamp': timezone.now().isoformat()
    }) 