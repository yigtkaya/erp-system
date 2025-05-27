# sales/admin.py
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from .models import SalesOrder, SalesOrderItem, SalesQuotation, SalesQuotationItem, OrderItemStatus, Shipping

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1
    fields = ('product', 'quantity', 'status', 'order_date', 'delivery_date', 'kapsam_deadline_date', 'notes')
    readonly_fields = ('is_overdue', 'is_kapsam_overdue')

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'status_summary_display', 'earliest_delivery_date', 'earliest_kapsam_deadline', 'kapsam_status', 'is_overdue', 'is_kapsam_overdue')
    search_fields = ('order_number', 'customer__name')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    inlines = [SalesOrderItemInline]
    
    def status_summary_display(self, obj):
        summary = obj.status_summary
        if not summary:
            return "No items"
        return ", ".join([f"{status}: {count}" for status, count in summary.items()])
    status_summary_display.short_description = 'Items Status Summary'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')

def update_delivery_dates(modeladmin, request, queryset):
    """Batch update delivery dates"""
    updated = queryset.update(delivery_date=timezone.now().date() + timezone.timedelta(days=30))
    modeladmin.message_user(request, f"Updated delivery dates for {updated} items.")
update_delivery_dates.short_description = "Update delivery dates (+30 days)"

def mark_as_urgent(modeladmin, request, queryset):
    """Mark items as urgent by updating kapsam deadline"""
    updated = queryset.update(kapsam_deadline_date=timezone.now().date() + timezone.timedelta(days=7))
    modeladmin.message_user(request, f"Marked {updated} items as urgent.")
mark_as_urgent.short_description = "Mark as urgent (7-day deadline)"

def confirm_items(modeladmin, request, queryset):
    """Confirm selected items"""
    updated = queryset.filter(status=OrderItemStatus.DRAFT).update(status=OrderItemStatus.CONFIRMED)
    modeladmin.message_user(request, f"Confirmed {updated} items.")
confirm_items.short_description = "Confirm items (DRAFT → CONFIRMED)"

def start_production(modeladmin, request, queryset):
    """Start production for selected items"""
    updated = queryset.filter(status=OrderItemStatus.CONFIRMED).update(status=OrderItemStatus.IN_PRODUCTION)
    modeladmin.message_user(request, f"Started production for {updated} items.")
start_production.short_description = "Start production (CONFIRMED → IN_PRODUCTION)"

def mark_ready(modeladmin, request, queryset):
    """Mark items as ready for shipment"""
    updated = queryset.filter(status=OrderItemStatus.IN_PRODUCTION).update(status=OrderItemStatus.READY)
    modeladmin.message_user(request, f"Marked {updated} items as ready.")
mark_ready.short_description = "Mark ready (IN_PRODUCTION → READY)"

def ship_items(modeladmin, request, queryset):
    """Ship selected items"""
    updated = queryset.filter(status=OrderItemStatus.READY).update(status=OrderItemStatus.SHIPPED)
    modeladmin.message_user(request, f"Shipped {updated} items.")
ship_items.short_description = "Ship items (READY → SHIPPED)"

def deliver_items(modeladmin, request, queryset):
    """Mark items as delivered"""
    updated = queryset.filter(status=OrderItemStatus.SHIPPED).update(status=OrderItemStatus.DELIVERED)
    modeladmin.message_user(request, f"Delivered {updated} items.")
deliver_items.short_description = "Deliver items (SHIPPED → DELIVERED)"

def export_items_csv(modeladmin, request, queryset):
    """Export selected items to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_order_items.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order Number', 'Product Code', 'Quantity', 'Status', 'Order Date', 'Delivery Date', 'Kapsam Deadline'])
    
    for item in queryset:
        writer.writerow([
            item.sales_order.order_number,
            item.product.stock_code,
            item.quantity,
            item.get_status_display(),
            item.order_date,
            item.delivery_date,
            item.kapsam_deadline_date
        ])
    
    return response
export_items_csv.short_description = "Export to CSV"

@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ('sales_order', 'product', 'quantity', 'status', 'order_date', 'delivery_date', 'kapsam_deadline_date', 'is_overdue', 'is_kapsam_overdue')
    search_fields = ('sales_order__order_number', 'product__stock_code', 'product__name')
    list_filter = ('status', 'order_date', 'delivery_date', 'kapsam_deadline_date')
    date_hierarchy = 'order_date'
    actions = [
        update_delivery_dates, mark_as_urgent, confirm_items, start_production, 
        mark_ready, ship_items, deliver_items, export_items_csv
    ]
    list_select_related = ['sales_order', 'product']
    
    # Enable bulk selection
    list_per_page = 50

@admin.register(SalesQuotation)
class SalesQuotationAdmin(admin.ModelAdmin):
    list_display = ('quotation_number', 'customer', 'quotation_date', 'valid_until', 'status')
    search_fields = ('quotation_number', 'customer__name')
    list_filter = ('status', 'quotation_date')
    date_hierarchy = 'quotation_date'

@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ('shipping_no', 'order', 'order_item', 'quantity', 'package_number', 'shipping_date')
    search_fields = ('shipping_no', 'order__order_number', 'order_item__product__stock_code')
    list_filter = ('shipping_date', 'package_number')
    date_hierarchy = 'shipping_date'
    list_select_related = ['order', 'order_item', 'order_item__product']
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            # Filter order_item choices to only show items from the selected order
            form.base_fields['order_item'].queryset = SalesOrderItem.objects.filter(sales_order=obj.order)
        return form
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "order_item":
            # This will be further filtered in get_form based on the selected order
            kwargs["queryset"] = SalesOrderItem.objects.select_related('product')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)