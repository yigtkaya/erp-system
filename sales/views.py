# sales/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Min, Max
from .models import SalesOrder, SalesOrderItem, SalesQuotation, SalesQuotationItem, OrderItemStatus
from .serializers import (
    SalesOrderSerializer, SalesOrderItemSerializer,
    SalesQuotationSerializer, SalesQuotationItemSerializer
)
from core.permissions import HasRolePermission
from datetime import timedelta


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['customer', 'salesperson']
    search_fields = ['order_number', 'customer__name', 'customer_po_number']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Override to add kapsam delivery date filtering and status filtering"""
        queryset = super().get_queryset()
        
        # Filter by order status (derived from items)
        order_status = self.request.query_params.get('status')
        if order_status:
            if order_status == OrderItemStatus.DELIVERED:
                # All items must be delivered
                queryset = queryset.filter(
                    items__status=OrderItemStatus.DELIVERED
                ).exclude(
                    items__status__in=[s for s in OrderItemStatus.values if s != OrderItemStatus.DELIVERED]
                ).distinct()
            elif order_status == OrderItemStatus.CANCELLED:
                # All items must be cancelled
                queryset = queryset.filter(
                    items__status=OrderItemStatus.CANCELLED
                ).exclude(
                    items__status__in=[s for s in OrderItemStatus.values if s != OrderItemStatus.CANCELLED]
                ).distinct()
            else:
                # At least one item has this status
                queryset = queryset.filter(items__status=order_status).distinct()
        
        # Filter by item status
        item_status = self.request.query_params.get('item_status')
        if item_status:
            queryset = queryset.filter(items__status=item_status).distinct()
        
        # Filter by kapsam delivery date range
        kapsam_date_from = self.request.query_params.get('kapsam_date_from')
        kapsam_date_to = self.request.query_params.get('kapsam_date_to')
        
        if kapsam_date_from:
            queryset = queryset.filter(items__kapsam_deadline_date__gte=kapsam_date_from).distinct()
        
        if kapsam_date_to:
            queryset = queryset.filter(items__kapsam_deadline_date__lte=kapsam_date_to).distinct()
        
        # Filter by kapsam overdue status
        kapsam_overdue = self.request.query_params.get('kapsam_overdue')
        if kapsam_overdue is not None:
            if kapsam_overdue.lower() in ['true', '1']:
                queryset = queryset.filter(
                    items__kapsam_deadline_date__lt=timezone.now().date()
                ).distinct()
            elif kapsam_overdue.lower() in ['false', '0']:
                queryset = queryset.filter(
                    Q(items__kapsam_deadline_date__gte=timezone.now().date()) |
                    Q(items__kapsam_deadline_date__isnull=True)
                ).distinct()
        
        # Filter by earliest kapsam deadline
        earliest_kapsam_before = self.request.query_params.get('earliest_kapsam_before')
        if earliest_kapsam_before:
            # Get orders where the earliest kapsam deadline is before the specified date
            queryset = queryset.annotate(
                earliest_kapsam=Min('items__kapsam_deadline_date')
            ).filter(earliest_kapsam__lt=earliest_kapsam_before)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(
            salesperson=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=False, methods=['get'])
    def kapsam_overdue(self, request):
        """Get all orders with overdue kapsam deadlines"""
        overdue_orders = self.get_queryset().filter(
            items__kapsam_deadline_date__lt=timezone.now().date(),
            items__status__in=[OrderItemStatus.CONFIRMED, OrderItemStatus.IN_PRODUCTION, OrderItemStatus.READY, OrderItemStatus.SHIPPED]
        ).distinct()
        
        serializer = self.get_serializer(overdue_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def kapsam_due_soon(self, request):
        """Get orders with kapsam deadlines due within specified days (default 7)"""
        days_ahead = int(request.query_params.get('days', 7))
        due_date = timezone.now().date() + timedelta(days=days_ahead)
        
        due_soon_orders = self.get_queryset().filter(
            items__kapsam_deadline_date__lte=due_date,
            items__kapsam_deadline_date__gte=timezone.now().date(),
            items__status__in=[OrderItemStatus.CONFIRMED, OrderItemStatus.IN_PRODUCTION, OrderItemStatus.READY]
        ).distinct()
        
        serializer = self.get_serializer(due_soon_orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def kapsam_summary(self, request):
        """Get summary of orders by kapsam deadline status"""
        today = timezone.now().date()
        
        # Count orders by kapsam status
        overdue_count = self.get_queryset().filter(
            items__kapsam_deadline_date__lt=today,
            items__status__in=[OrderItemStatus.CONFIRMED, OrderItemStatus.IN_PRODUCTION, OrderItemStatus.READY, OrderItemStatus.SHIPPED]
        ).distinct().count()
        
        due_this_week = self.get_queryset().filter(
            items__kapsam_deadline_date__gte=today,
            items__kapsam_deadline_date__lt=today + timedelta(days=7),
            items__status__in=[OrderItemStatus.CONFIRMED, OrderItemStatus.IN_PRODUCTION, OrderItemStatus.READY]
        ).distinct().count()
        
        due_next_week = self.get_queryset().filter(
            items__kapsam_deadline_date__gte=today + timedelta(days=7),
            items__kapsam_deadline_date__lt=today + timedelta(days=14),
            items__status__in=[OrderItemStatus.CONFIRMED, OrderItemStatus.IN_PRODUCTION, OrderItemStatus.READY]
        ).distinct().count()
        
        return Response({
            'overdue': overdue_count,
            'due_this_week': due_this_week,
            'due_next_week': due_next_week,
            'summary_date': today
        })

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        
        # Check if any items are not in DRAFT status
        non_draft_items = order.items.exclude(status=OrderItemStatus.DRAFT)
        if non_draft_items.exists():
            return Response(
                {'error': 'Only orders with all items in DRAFT status can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Update all items to CONFIRMED
            order.items.update(status=OrderItemStatus.CONFIRMED)
            
            # Create work orders for manufactured products
            from manufacturing.models import WorkOrder
            for item in order.items.filter(product__product_type__in=['MONTAGED', 'SEMI']):
                WorkOrder.objects.create(
                    product=item.product,
                    quantity_ordered=item.quantity,
                    planned_start_date=timezone.now(),
                    planned_end_date=item.delivery_date,
                    sales_order=order,
                    status='DRAFT',
                    priority='MEDIUM',
                    created_by=request.user
                )
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        # Check if any items are already delivered
        delivered_items = order.items.filter(status=OrderItemStatus.DELIVERED)
        if delivered_items.exists():
            return Response(
                {'error': 'Cannot cancel orders with delivered items'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Update all non-delivered items to CANCELLED
            order.items.exclude(status=OrderItemStatus.DELIVERED).update(status=OrderItemStatus.CANCELLED)
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_with_items(self, request):
        """Create order with items in a single transaction"""
        with transaction.atomic():
            items_data = request.data.pop('items', [])
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            order = serializer.save(
                salesperson=request.user,
                created_by=request.user
            )
            
            # Create order items
            for item_data in items_data:
                item_data['sales_order'] = order.id
                item_serializer = SalesOrderItemSerializer(data=item_data)
                item_serializer.is_valid(raise_exception=True)
                item_serializer.save()
            
            return Response(
                self.get_serializer(order).data,
                status=status.HTTP_201_CREATED
            )


class SalesQuotationViewSet(viewsets.ModelViewSet):
    queryset = SalesQuotation.objects.all()
    serializer_class = SalesQuotationSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['status', 'customer', 'salesperson']
    search_fields = ['quotation_number', 'customer__name']
    ordering_fields = ['quotation_date', 'created_at']
    ordering = ['-quotation_date']
    
    def perform_create(self, serializer):
        serializer.save(
            salesperson=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def convert_to_order(self, request, pk=None):
        quotation = self.get_object()
        
        if quotation.status != 'ACCEPTED':
            return Response(
                {'error': 'Only accepted quotations can be converted to orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if quotation.converted_to_order:
            return Response(
                {'error': 'Quotation already converted to order'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create sales order
            order = SalesOrder.objects.create(
                customer=quotation.customer,
                status='CONFIRMED',
                salesperson=request.user,
                shipping_address=quotation.customer.address,
                billing_address=quotation.customer.address,
                notes=f"Created from quotation {quotation.quotation_number}",
                created_by=request.user
            )
            
            # Copy quotation items to order items
            default_delivery_date = timezone.now().date() + timezone.timedelta(days=30)
            default_kapsam_deadline = timezone.now().date() + timezone.timedelta(days=20)
            
            for quote_item in quotation.items.all():
                SalesOrderItem.objects.create(
                    sales_order=order,
                    product=quote_item.product,
                    quantity=quote_item.quantity,
                    order_date=timezone.now().date(),
                    delivery_date=default_delivery_date,
                    kapsam_deadline_date=default_kapsam_deadline,
                    notes=quote_item.notes
                )
            
            # Link quotation to order
            quotation.converted_to_order = order
            quotation.save()
            
            return Response(
                SalesOrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )


class SalesOrderItemViewSet(viewsets.ModelViewSet):
    queryset = SalesOrderItem.objects.all()
    serializer_class = SalesOrderItemSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['sales_order', 'product', 'order_date', 'delivery_date', 'status']
    search_fields = ['sales_order__order_number', 'product__product_code']
    ordering_fields = ['order_date', 'delivery_date', 'created_at']
    ordering = ['order_date']
    
    @action(detail=False, methods=['post'])
    def batch_update_status(self, request):
        """Batch update status for multiple order items"""
        item_ids = request.data.get('item_ids', [])
        new_status = request.data.get('status')
        
        if not item_ids:
            return Response(
                {'error': 'item_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not new_status or new_status not in OrderItemStatus.values:
            return Response(
                {'error': f'Valid status required. Options: {list(OrderItemStatus.values)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            updated_count = self.queryset.filter(id__in=item_ids).update(status=new_status)
            
            # If status is CONFIRMED, create work orders for manufactured products
            if new_status == OrderItemStatus.CONFIRMED:
                from manufacturing.models import WorkOrder
                items = self.queryset.filter(id__in=item_ids, product__product_type__in=['MONTAGED', 'SEMI'])
                for item in items:
                    WorkOrder.objects.get_or_create(
                        product=item.product,
                        sales_order=item.sales_order,
                        defaults={
                            'quantity_ordered': item.quantity,
                            'planned_start_date': timezone.now(),
                            'planned_end_date': item.delivery_date,
                            'status': 'DRAFT',
                            'priority': 'MEDIUM',
                            'created_by': request.user
                        }
                    )
            
            return Response({
                'message': f'Updated {updated_count} items to {new_status}',
                'status': new_status
            })
    
    @action(detail=False, methods=['post'])
    def batch_advance_status(self, request):
        """Advance status for multiple items to next logical status"""
        item_ids = request.data.get('item_ids', [])
        
        if not item_ids:
            return Response(
                {'error': 'item_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Define status progression
        status_progression = {
            OrderItemStatus.DRAFT: OrderItemStatus.CONFIRMED,
            OrderItemStatus.CONFIRMED: OrderItemStatus.IN_PRODUCTION,
            OrderItemStatus.IN_PRODUCTION: OrderItemStatus.READY,
            OrderItemStatus.READY: OrderItemStatus.SHIPPED,
            OrderItemStatus.SHIPPED: OrderItemStatus.DELIVERED,
        }
        
        with transaction.atomic():
            items = self.queryset.filter(id__in=item_ids)
            updated_items = []
            
            for item in items:
                if item.status in status_progression:
                    new_status = status_progression[item.status]
                    item.status = new_status
                    item.save()
                    updated_items.append({
                        'id': item.id,
                        'old_status': list(status_progression.keys())[list(status_progression.values()).index(new_status)],
                        'new_status': new_status
                    })
            
            return Response({
                'message': f'Advanced status for {len(updated_items)} items',
                'updated_items': updated_items
            })
    
    @action(detail=False, methods=['get'])
    def by_status(self, request):
        """Get items grouped by status"""
        status_param = request.query_params.get('status')
        if status_param:
            items = self.queryset.filter(status=status_param)
        else:
            items = self.queryset.all()
        
        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def status_summary(self, request):
        """Get summary of items by status"""
        from django.db.models import Count
        
        summary = dict(
            self.queryset.values('status')
            .annotate(count=Count('status'))
            .values_list('status', 'count')
        )
        
        # Add human-readable labels
        summary_with_labels = {}
        for status_code, count in summary.items():
            status_obj = OrderItemStatus(status_code)
            summary_with_labels[status_code] = {
                'count': count,
                'label': status_obj.label
            }
        
        return Response(summary_with_labels)

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """Batch update multiple order items"""
        item_ids = request.data.get('item_ids', [])
        update_data = request.data.get('update_data', {})
        
        if not item_ids:
            return Response(
                {'error': 'item_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate update_data contains only allowed fields
        allowed_fields = ['delivery_date', 'kapsam_deadline_date', 'notes', 'quantity', 'status']
        update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not update_fields:
            return Response(
                {'error': 'No valid update fields provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status if provided
        if 'status' in update_fields and update_fields['status'] not in OrderItemStatus.values:
            return Response(
                {'error': f'Invalid status. Options: {list(OrderItemStatus.values)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            updated_count = self.queryset.filter(id__in=item_ids).update(**update_fields)
            
            return Response({
                'message': f'Updated {updated_count} items',
                'updated_fields': list(update_fields.keys())
            })
    
    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """Batch delete multiple order items"""
        item_ids = request.data.get('item_ids', [])
        
        if not item_ids:
            return Response(
                {'error': 'item_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            deleted_count, _ = self.queryset.filter(id__in=item_ids).delete()
            
            return Response({
                'message': f'Deleted {deleted_count} items'
            })
    
    @action(detail=False, methods=['post'])
    def batch_reschedule(self, request):
        """Batch reschedule delivery dates with offset"""
        item_ids = request.data.get('item_ids', [])
        days_offset = request.data.get('days_offset', 0)
        
        if not item_ids:
            return Response(
                {'error': 'item_ids required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            days_offset = int(days_offset)
        except (ValueError, TypeError):
            return Response(
                {'error': 'days_offset must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            items = self.queryset.filter(id__in=item_ids)
            
            for item in items:
                item.delivery_date = item.delivery_date + timedelta(days=days_offset)
                if item.kapsam_deadline_date:
                    item.kapsam_deadline_date = item.kapsam_deadline_date + timedelta(days=days_offset)
                item.save()
            
            return Response({
                'message': f'Rescheduled {items.count()} items by {days_offset} days'
            })
    
    @action(detail=False, methods=['get'])
    def overdue_items(self, request):
        """Get all overdue items"""
        overdue_items = self.queryset.filter(
            delivery_date__lt=timezone.now().date(),
            sales_order__status__in=['CONFIRMED', 'IN_PRODUCTION', 'READY', 'SHIPPED']
        )
        
        serializer = self.get_serializer(overdue_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_bulk(self, request):
        """Create multiple order items in bulk"""
        items_data = request.data.get('items', [])
        
        if not items_data:
            return Response(
                {'error': 'items data required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            created_items = []
            
            for item_data in items_data:
                serializer = self.get_serializer(data=item_data)
                serializer.is_valid(raise_exception=True)
                item = serializer.save()
                created_items.append(item)
            
            return Response(
                self.get_serializer(created_items, many=True).data,
                status=status.HTTP_201_CREATED
            )