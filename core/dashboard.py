from django.db.models import Sum, Count, Avg, Q, F, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from inventory.models import Product
from sales.models import SalesOrder, SalesOrderItem
from purchasing.models import PurchaseOrder, PurchaseOrderItem
from manufacturing.models import WorkOrder, ProductionOutput
from quality.models import QualityInspection, NonConformance
from maintenance.models import Equipment, MaintenanceWorkOrder
import logging

logger = logging.getLogger(__name__)

class DashboardService:
    @staticmethod
    def get_overview_stats(reference_date=None, period='monthly'):
        """
        Get overview statistics for dashboard
        
        Args:
            reference_date: Date to use as reference (defaults to today)
            period: Time period for metrics (daily, weekly, monthly, yearly)
        
        Returns:
            Dictionary with consolidated stats from all modules
        """
        if reference_date is None:
            reference_date = timezone.now().date()
        
        # Calculate period start dates based on reference date
        if period == 'daily':
            period_start = reference_date
            prev_period_start = reference_date - timedelta(days=1)
            prev_period_end = prev_period_start
        elif period == 'weekly':
            # Start from Monday of the week
            weekday = reference_date.weekday()
            period_start = reference_date - timedelta(days=weekday)
            prev_period_start = period_start - timedelta(days=7) 
            prev_period_end = period_start - timedelta(days=1)
        elif period == 'yearly':
            period_start = reference_date.replace(month=1, day=1)
            prev_period_start = period_start.replace(year=period_start.year-1)
            prev_period_end = period_start - timedelta(days=1)
        else:  # monthly (default)
            period_start = reference_date.replace(day=1)
            last_month = reference_date.month - 1 or 12
            last_month_year = reference_date.year if reference_date.month > 1 else reference_date.year - 1
            prev_period_start = reference_date.replace(year=last_month_year, month=last_month, day=1)
            # Last day of previous month
            if last_month == 12:
                prev_period_end = reference_date.replace(year=last_month_year, month=last_month, day=31)
            else:
                prev_period_end = period_start - timedelta(days=1)
        
        try:
            stats = {
                'inventory': DashboardService._get_inventory_stats(),
                'sales': DashboardService._get_sales_stats(period_start),
                'production': DashboardService._get_production_stats(period_start),
                'quality': DashboardService._get_quality_stats(period_start),
                'maintenance': DashboardService._get_maintenance_stats(),
                'purchasing': DashboardService._get_purchasing_stats(period_start),
                'trends': DashboardService._get_trend_data(period_start, prev_period_start, prev_period_end),
                'metadata': {
                    'period': period,
                    'reference_date': reference_date.isoformat(),
                    'period_start': period_start.isoformat(),
                    'prev_period_start': prev_period_start.isoformat(),
                    'prev_period_end': prev_period_end.isoformat(),
                    'generated_at': timezone.now().isoformat(),
                }
            }
            
            return stats
        except Exception as e:
            logger.error(f"Dashboard stats error: {str(e)}")
            raise
    
    @staticmethod
    def _get_inventory_stats():
        """Get inventory statistics"""
        products = Product.objects.filter(is_active=True)
        
        return {
            'total_products': products.count(),
            'low_stock_items': products.filter(
                current_stock__lte=F('reorder_point')
            ).count(),
            'out_of_stock': products.filter(current_stock=0).count(),
            'total_stock_value': products.aggregate(
                total=Coalesce(Sum(F('current_stock') * F('unit_cost')), Value(0))
            )['total'],
            'categories': products.values('inventory_category__name').annotate(
                count=Count('id')
            ),
        }
    
    @staticmethod
    def _get_sales_stats(month_start):
        """Get sales statistics"""
        orders = SalesOrder.objects.filter(
            order_date__gte=month_start
        )
        
        # Get top customers
        top_customers = SalesOrder.objects.filter(
            order_date__gte=month_start
        ).values('customer__name').annotate(
            total_amount=Sum('total_amount'),
            order_count=Count('id')
        ).order_by('-total_amount')[:5]
        
        return {
            'monthly_orders': orders.count(),
            'monthly_revenue': orders.aggregate(
                total=Coalesce(Sum('total_amount'), Value(0))
            )['total'],
            'pending_orders': SalesOrder.objects.filter(
                status__in=['CONFIRMED', 'IN_PRODUCTION']
            ).count(),
            'overdue_orders': SalesOrder.objects.filter(
                status__in=['CONFIRMED', 'IN_PRODUCTION'],
                delivery_date__lt=timezone.now().date()
            ).count(),
            'order_status_breakdown': SalesOrder.objects.values('status').annotate(
                count=Count('id')
            ),
            'top_customers': list(top_customers),
        }
    
    @staticmethod
    def _get_production_stats(month_start):
        """Get production statistics"""
        work_orders = WorkOrder.objects.filter(
            created_at__gte=month_start
        )
        
        completed_orders = work_orders.filter(status='COMPLETED')
        
        efficiency = 0
        if completed_orders.exists():
            total_planned = completed_orders.aggregate(
                total=Coalesce(Sum('quantity_ordered'), Value(0))
            )['total']
            total_actual = completed_orders.aggregate(
                total=Coalesce(Sum('quantity_completed'), Value(0))
            )['total']
            
            if total_planned > 0:
                efficiency = (total_actual / total_planned) * 100
        
        return {
            'active_work_orders': WorkOrder.objects.filter(
                status='IN_PROGRESS'
            ).count(),
            'monthly_work_orders': work_orders.count(),
            'completed_orders': completed_orders.count(),
            'production_efficiency': round(efficiency, 2),
            'total_output': ProductionOutput.objects.filter(
                output_date__gte=month_start
            ).aggregate(
                total=Coalesce(Sum('quantity_good'), Value(0))
            )['total'],
            'work_order_status': WorkOrder.objects.values('status').annotate(
                count=Count('id')
            ),
        }
    
    @staticmethod
    def _get_quality_stats(month_start):
        """Get quality statistics"""
        inspections = QualityInspection.objects.filter(
            inspection_date__gte=month_start
        )
        
        total_inspections = inspections.count()
        passed_inspections = inspections.filter(result='PASS').count()
        
        pass_rate = 0
        if total_inspections > 0:
            pass_rate = (passed_inspections / total_inspections) * 100
        
        return {
            'monthly_inspections': total_inspections,
            'pass_rate': round(pass_rate, 2),
            'failed_inspections': inspections.filter(result='FAIL').count(),
            'open_nonconformances': NonConformance.objects.filter(
                status__in=['OPEN', 'INVESTIGATING']
            ).count(),
            'nc_by_severity': NonConformance.objects.filter(
                created_at__gte=month_start
            ).values('severity').annotate(count=Count('id')),
            'inspection_results': inspections.values('result').annotate(
                count=Count('id')
            ),
        }
    
    @staticmethod
    def _get_maintenance_stats():
        """Get maintenance statistics"""
        today = timezone.now()
        
        overdue_maintenance = MaintenanceWorkOrder.objects.filter(
            status='SCHEDULED',
            scheduled_end__lt=today
        )
        
        upcoming_maintenance = MaintenanceWorkOrder.objects.filter(
            status='SCHEDULED',
            scheduled_start__gte=today,
            scheduled_start__lte=today + timedelta(days=7)
        )
        
        return {
            'total_equipment': Equipment.objects.filter(is_active=True).count(),
            'overdue_maintenance': overdue_maintenance.count(),
            'upcoming_maintenance': upcoming_maintenance.count(),
            'in_progress_maintenance': MaintenanceWorkOrder.objects.filter(
                status='IN_PROGRESS'
            ).count(),
            'maintenance_by_type': MaintenanceWorkOrder.objects.values(
                'maintenance_type'
            ).annotate(count=Count('id')),
            'critical_equipment': overdue_maintenance.filter(
                equipment__is_critical=True
            ).count(),
        }
    
    @staticmethod
    def _get_purchasing_stats(month_start):
        """Get purchasing statistics"""
        purchase_orders = PurchaseOrder.objects.filter(
            order_date__gte=month_start
        )
        
        return {
            'monthly_pos': purchase_orders.count(),
            'monthly_spending': purchase_orders.aggregate(
                total=Coalesce(Sum('total_amount'), Value(0))
            )['total'],
            'pending_pos': PurchaseOrder.objects.filter(
                status__in=['APPROVED', 'SENT']
            ).count(),
            'overdue_deliveries': PurchaseOrder.objects.filter(
                status__in=['APPROVED', 'SENT', 'PARTIAL'],
                expected_delivery_date__lt=timezone.now().date()
            ).count(),
            'po_status_breakdown': PurchaseOrder.objects.values('status').annotate(
                count=Count('id')
            ),
            'top_suppliers': PurchaseOrder.objects.filter(
                order_date__gte=month_start
            ).values('supplier__name').annotate(
                total_amount=Sum('total_amount'),
                order_count=Count('id')
            ).order_by('-total_amount')[:5],
        }
    
    @staticmethod
    def _get_trend_data(month_start, last_month_start, last_month_end):
        """Get month-over-month trends"""
        current_revenue = SalesOrder.objects.filter(
            order_date__gte=month_start
        ).aggregate(total=Coalesce(Sum('total_amount'), Value(0)))['total']
        
        last_month_revenue = SalesOrder.objects.filter(
            order_date__gte=last_month_start,
            order_date__lte=last_month_end
        ).aggregate(total=Coalesce(Sum('total_amount'), Value(0)))['total']
        
        revenue_trend = 0
        if last_month_revenue > 0:
            revenue_trend = ((current_revenue - last_month_revenue) / last_month_revenue) * 100
        
        return {
            'revenue_trend': round(revenue_trend, 2),
            'current_month_revenue': current_revenue,
            'last_month_revenue': last_month_revenue,
            'daily_sales': DashboardService._get_daily_sales_data(),
            'production_trend': DashboardService._get_production_trend(),
        }
    
    @staticmethod
    def _get_daily_sales_data():
        """Get daily sales data for the current month"""
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        daily_sales = SalesOrder.objects.filter(
            order_date__gte=month_start
        ).values('order_date').annotate(
            amount=Sum('total_amount'),
            count=Count('id')
        ).order_by('order_date')
        
        return list(daily_sales)
    
    @staticmethod
    def _get_production_trend():
        """Get production trend data"""
        last_30_days = []
        today = timezone.now().date()
        
        for i in range(30):
            date = today - timedelta(days=i)
            output = ProductionOutput.objects.filter(
                output_date__date=date
            ).aggregate(
                total=Coalesce(Sum('quantity_good'), Value(0))
            )['total']
            
            last_30_days.append({
                'date': date,
                'output': output
            })
        
        return list(reversed(last_30_days))

    @staticmethod
    def get_module_stats(module, reference_date=None, period='monthly'):
        """
        Get statistics for a specific module
        
        Args:
            module: Module name (inventory, sales, etc)
            reference_date: Date to use as reference
            period: Time period for metrics
            
        Returns:
            Dictionary with module-specific stats
        """
        if reference_date is None:
            reference_date = timezone.now().date()
            
        # Calculate period start based on reference date and period
        if period == 'daily':
            period_start = reference_date
        elif period == 'weekly':
            # Start from Monday of the week
            weekday = reference_date.weekday()
            period_start = reference_date - timedelta(days=weekday)
        elif period == 'yearly':
            period_start = reference_date.replace(month=1, day=1)
        else:  # monthly (default)
            period_start = reference_date.replace(day=1)
            
        try:
            if module == 'inventory':
                return DashboardService._get_inventory_stats()
            elif module == 'sales':
                return DashboardService._get_sales_stats(period_start)
            elif module == 'production':
                return DashboardService._get_production_stats(period_start)
            elif module == 'quality':
                return DashboardService._get_quality_stats(period_start)
            elif module == 'maintenance':
                return DashboardService._get_maintenance_stats()
            elif module == 'purchasing':
                return DashboardService._get_purchasing_stats(period_start)
            elif module == 'trends':
                # Calculate previous period dates
                if period == 'daily':
                    prev_period_start = reference_date - timedelta(days=1)
                    prev_period_end = prev_period_start
                elif period == 'weekly':
                    prev_period_start = period_start - timedelta(days=7) 
                    prev_period_end = period_start - timedelta(days=1)
                elif period == 'yearly':
                    prev_period_start = period_start.replace(year=period_start.year-1)
                    prev_period_end = period_start - timedelta(days=1)
                else:  # monthly
                    last_month = reference_date.month - 1 or 12
                    last_month_year = reference_date.year if reference_date.month > 1 else reference_date.year - 1
                    prev_period_start = reference_date.replace(year=last_month_year, month=last_month, day=1)
                    # Last day of previous month
                    if last_month == 12:
                        prev_period_end = reference_date.replace(year=last_month_year, month=last_month, day=31)
                    else:
                        prev_period_end = period_start - timedelta(days=1)
                
                return DashboardService._get_trend_data(period_start, prev_period_start, prev_period_end)
            else:
                raise ValueError(f"Unknown module: {module}")
        except Exception as e:
            logger.error(f"Module stats error for {module}: {str(e)}")
            raise