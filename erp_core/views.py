from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    """
    Main dashboard view for the ERP system
    """
    context = {
        'title': 'ERP System Dashboard'
    }
    return render(request, 'erp_core/home.html', context) 