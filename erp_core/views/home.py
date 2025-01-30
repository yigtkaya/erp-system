from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from erp_core.models import User, Department
from inventory.models import Product, RawMaterial
from sales.models import SalesOrder
from manufacturing.models import WorkOrder

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