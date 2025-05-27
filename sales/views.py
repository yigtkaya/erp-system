# sales/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Min, Max, Sum
from .models import SalesOrder, SalesOrderItem, SalesQuotation, SalesQuotationItem, OrderItemStatus, Shipping
from .serializers import (
    SalesOrderSerializer, SalesOrderItemSerializer,
    SalesQuotationSerializer, SalesQuotationItemSerializer,
    BatchDeleteSerializer, BatchUpdateSerializer, BatchAddItemSerializer,
    BatchRescheduleSerializer, BatchStatusUpdateSerializer, BatchOperationResponseSerializer,
    ShippingSerializer, ShippingListSerializer
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
    def batch_update_items(self, request, pk=None):
        """Batch update items within a specific sales order"""
        order = self.get_object()
        serializer = BatchUpdateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        item_ids = serializer.validated_data['item_ids']
        update_data = serializer.validated_data['update_data']
        
        with transaction.atomic():
            # Only update items that belong to this order
            items = order.items.filter(id__in=item_ids)
            found_count = items.count()
            
            if found_count == 0:
                return Response({
                    'success': False,
                    'message': 'No items found with provided IDs in this order',
                    'affected_count': 0
                }, status=status.HTTP_404_NOT_FOUND)
            
            updated_count = items.update(**update_data)
            
            return Response({
                'success': True,
                'message': f'Successfully updated {updated_count} items in order {order.order_number}',
                'affected_count': updated_count,
                'details': {
                    'order_number': order.order_number,
                    'updated_fields': list(update_data.keys()),
                    'requested_items': len(item_ids),
                    'found_items': found_count
                }
            })

    @action(detail=True, methods=['post'])
    def batch_delete_items(self, request, pk=None):
        """Batch delete items within a specific sales order"""
        order = self.get_object()
        serializer = BatchDeleteSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        item_ids = serializer.validated_data['item_ids']
        
        with transaction.atomic():
            # Only delete items that belong to this order
            items = order.items.filter(id__in=item_ids)
            found_count = items.count()
            
            if found_count == 0:
                return Response({
                    'success': False,
                    'message': 'No items found with provided IDs in this order',
                    'affected_count': 0
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check for protected items
            protected_items = items.filter(status__in=[OrderItemStatus.DELIVERED, OrderItemStatus.SHIPPED])
            if protected_items.exists():
                return Response({
                    'success': False,
                    'message': f'Cannot delete {protected_items.count()} items that are shipped or delivered',
                    'affected_count': 0,
                    'details': {
                        'protected_items': list(protected_items.values_list('id', flat=True))
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            deleted_count, _ = items.delete()
            
            return Response({
                'success': True,
                'message': f'Successfully deleted {deleted_count} items from order {order.order_number}',
                'affected_count': deleted_count,
                'details': {
                    'order_number': order.order_number,
                    'requested_items': len(item_ids),
                    'found_items': found_count
                }
            })

    @action(detail=True, methods=['post'])
    def add_items(self, request, pk=None):
        """Add multiple items to this specific sales order"""
        order = self.get_object()
        items_data = request.data.get('items', [])
        
        if not items_data:
            return Response({
                'success': False,
                'message': 'items data required',
                'affected_count': 0
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a modified request data with the order ID
        batch_data = {
            'sales_order_id': order.id,
            'items': items_data
        }
        
        serializer = BatchAddItemSerializer(data=batch_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_items = serializer.validated_data['items']
        
        with transaction.atomic():
            created_items = []
            
            for item_data in validated_items:
                sales_order_item = SalesOrderItem.objects.create(
                    sales_order=order,
                    product_id=item_data['product_id'],
                    quantity=item_data['quantity'],
                    order_date=item_data['order_date'],
                    delivery_date=item_data['delivery_date'],
                    kapsam_deadline_date=item_data.get('kapsam_deadline_date'),
                    notes=item_data.get('notes', ''),
                    status=item_data['status']
                )
                created_items.append(sales_order_item)
            
            response_serializer = SalesOrderItemSerializer(created_items, many=True)
            
            return Response({
                'success': True,
                'message': f'Successfully added {len(created_items)} items to order {order.order_number}',
                'affected_count': len(created_items),
                'details': {
                    'order_number': order.order_number,
                    'created_items': response_serializer.data
                }
            }, status=status.HTTP_201_CREATED)
    
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
    search_fields = ['sales_order__order_number', 'product__stock_code']
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
        """Enhanced batch update multiple order items"""
        serializer = BatchUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        item_ids = serializer.validated_data['item_ids']
        update_data = serializer.validated_data['update_data']
        
        with transaction.atomic():
            # Get items to update and validate they exist
            items = self.queryset.filter(id__in=item_ids)
            found_count = items.count()
            
            if found_count == 0:
                return Response({
                    'success': False,
                    'message': 'No items found with provided IDs',
                    'affected_count': 0
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Perform update
            updated_count = items.update(**update_data)
            
            # Prepare response data
            response_data = {
                'success': True,
                'message': f'Successfully updated {updated_count} items',
                'affected_count': updated_count,
                'details': {
                    'updated_fields': list(update_data.keys()),
                    'requested_items': len(item_ids),
                    'found_items': found_count
                }
            }
            
            if found_count != len(item_ids):
                response_data['details']['missing_ids'] = list(
                    set(item_ids) - set(items.values_list('id', flat=True))
                )
            
            return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """Enhanced batch delete multiple order items with safety checks"""
        serializer = BatchDeleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        item_ids = serializer.validated_data['item_ids']
        
        with transaction.atomic():
            # Get items to delete and validate they exist
            items = self.queryset.filter(id__in=item_ids)
            found_count = items.count()
            
            if found_count == 0:
                return Response({
                    'success': False,
                    'message': 'No items found with provided IDs',
                    'affected_count': 0
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check for items that shouldn't be deleted (e.g., delivered items)
            protected_items = items.filter(status__in=[OrderItemStatus.DELIVERED, OrderItemStatus.SHIPPED])
            if protected_items.exists():
                protected_count = protected_items.count()
                return Response({
                    'success': False,
                    'message': f'Cannot delete {protected_count} items that are shipped or delivered',
                    'affected_count': 0,
                    'details': {
                        'protected_items': list(protected_items.values_list('id', flat=True)),
                        'protected_statuses': [OrderItemStatus.DELIVERED, OrderItemStatus.SHIPPED]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Store item details for response before deletion
            item_details = list(items.values('id', 'sales_order__order_number', 'product__stock_code'))
            
            # Perform deletion
            deleted_count, _ = items.delete()
            
            response_data = {
                'success': True,
                'message': f'Successfully deleted {deleted_count} items',
                'affected_count': deleted_count,
                'details': {
                    'requested_items': len(item_ids),
                    'found_items': found_count,
                    'deleted_items': item_details
                }
            }
            
            if found_count != len(item_ids):
                response_data['details']['missing_ids'] = list(
                    set(item_ids) - set([item['id'] for item in item_details])
                )
            
            return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def batch_reschedule(self, request):
        """Enhanced batch reschedule delivery dates with offset"""
        serializer = BatchRescheduleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        item_ids = serializer.validated_data['item_ids']
        days_offset = serializer.validated_data['days_offset']
        update_kapsam = serializer.validated_data['update_kapsam']
        
        with transaction.atomic():
            items = self.queryset.filter(id__in=item_ids)
            found_count = items.count()
            
            if found_count == 0:
                return Response({
                    'success': False,
                    'message': 'No items found with provided IDs',
                    'affected_count': 0
                }, status=status.HTTP_404_NOT_FOUND)
            
            rescheduled_items = []
            
            for item in items:
                old_delivery_date = item.delivery_date
                old_kapsam_date = item.kapsam_deadline_date
                
                item.delivery_date = item.delivery_date + timedelta(days=days_offset)
                
                if update_kapsam and item.kapsam_deadline_date:
                    item.kapsam_deadline_date = item.kapsam_deadline_date + timedelta(days=days_offset)
                
                item.save()
                
                rescheduled_items.append({
                    'id': item.id,
                    'old_delivery_date': old_delivery_date.isoformat(),
                    'new_delivery_date': item.delivery_date.isoformat(),
                    'old_kapsam_date': old_kapsam_date.isoformat() if old_kapsam_date else None,
                    'new_kapsam_date': item.kapsam_deadline_date.isoformat() if item.kapsam_deadline_date else None
                })
            
            response_data = {
                'success': True,
                'message': f'Successfully rescheduled {found_count} items by {days_offset} days',
                'affected_count': found_count,
                'details': {
                    'days_offset': days_offset,
                    'update_kapsam': update_kapsam,
                    'rescheduled_items': rescheduled_items,
                    'requested_items': len(item_ids),
                    'found_items': found_count
                }
            }
            
            if found_count != len(item_ids):
                response_data['details']['missing_ids'] = list(
                    set(item_ids) - set(items.values_list('id', flat=True))
                )
            
            return Response(response_data)
    
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
    def batch_add_items(self, request):
        """Add multiple items to a sales order in batch"""
        serializer = BatchAddItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        sales_order_id = serializer.validated_data['sales_order_id']
        items_data = serializer.validated_data['items']
        
        with transaction.atomic():
            sales_order = SalesOrder.objects.get(id=sales_order_id)
            created_items = []
            
            for item_data in items_data:
                # Create the sales order item
                sales_order_item = SalesOrderItem.objects.create(
                    sales_order=sales_order,
                    product_id=item_data['product_id'],
                    quantity=item_data['quantity'],
                    order_date=item_data['order_date'],
                    delivery_date=item_data['delivery_date'],
                    kapsam_deadline_date=item_data.get('kapsam_deadline_date'),
                    notes=item_data.get('notes', ''),
                    status=item_data['status']
                )
                created_items.append(sales_order_item)
            
            # Serialize the created items for response
            response_serializer = SalesOrderItemSerializer(created_items, many=True)
            
            return Response({
                'success': True,
                'message': f'Successfully added {len(created_items)} items to order {sales_order.order_number}',
                'affected_count': len(created_items),
                'details': {
                    'sales_order_id': sales_order_id,
                    'sales_order_number': sales_order.order_number,
                    'created_items': response_serializer.data
                }
            }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def batch_status_update(self, request):
        """Enhanced batch status update with validation"""
        serializer = BatchStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        item_ids = serializer.validated_data['item_ids']
        new_status = serializer.validated_data['new_status']
        force_update = serializer.validated_data['force_update']
        
        # Define valid status transitions
        valid_transitions = {
            OrderItemStatus.DRAFT: [OrderItemStatus.CONFIRMED, OrderItemStatus.CANCELLED],
            OrderItemStatus.CONFIRMED: [OrderItemStatus.IN_PRODUCTION, OrderItemStatus.CANCELLED],
            OrderItemStatus.IN_PRODUCTION: [OrderItemStatus.READY, OrderItemStatus.CANCELLED],
            OrderItemStatus.READY: [OrderItemStatus.SHIPPED, OrderItemStatus.CANCELLED],
            OrderItemStatus.SHIPPED: [OrderItemStatus.DELIVERED],
            OrderItemStatus.DELIVERED: [],  # Final status
            OrderItemStatus.CANCELLED: [OrderItemStatus.DRAFT]  # Can reactivate cancelled items
        }
        
        with transaction.atomic():
            items = self.queryset.filter(id__in=item_ids)
            found_count = items.count()
            
            if found_count == 0:
                return Response({
                    'success': False,
                    'message': 'No items found with provided IDs',
                    'affected_count': 0
                }, status=status.HTTP_404_NOT_FOUND)
            
            updated_items = []
            invalid_transitions = []
            
            for item in items:
                old_status = item.status
                
                # Check if transition is valid
                if not force_update:
                    if new_status not in valid_transitions.get(old_status, []):
                        invalid_transitions.append({
                            'item_id': item.id,
                            'current_status': old_status,
                            'requested_status': new_status,
                            'valid_transitions': valid_transitions.get(old_status, [])
                        })
                        continue
                
                # Update status
                item.status = new_status
                item.save()
                
                updated_items.append({
                    'id': item.id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'product_code': item.product.stock_code,
                    'sales_order': item.sales_order.order_number
                })
            
            response_data = {
                'success': len(updated_items) > 0,
                'message': f'Successfully updated status for {len(updated_items)} items',
                'affected_count': len(updated_items),
                'details': {
                    'new_status': new_status,
                    'force_update': force_update,
                    'updated_items': updated_items,
                    'requested_items': len(item_ids),
                    'found_items': found_count
                }
            }
            
            if invalid_transitions:
                response_data['details']['invalid_transitions'] = invalid_transitions
                if not force_update:
                    response_data['message'] += f'. {len(invalid_transitions)} items had invalid status transitions.'
            
            if found_count != len(item_ids):
                response_data['details']['missing_ids'] = list(
                    set(item_ids) - set(items.values_list('id', flat=True))
                )
            
            return Response(response_data)

    @action(detail=False, methods=['post'])
    def create_bulk(self, request):
        """Create multiple order items in bulk (legacy method)"""
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
            
            return Response({
                'success': True,
                'message': f'Created {len(created_items)} order items',
                'created_count': len(created_items),
                'created_items': [SalesOrderItemSerializer(item).data for item in created_items]
            })


class ShippingViewSet(viewsets.ModelViewSet):
    queryset = Shipping.objects.all()
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['order', 'order_item', 'shipping_date', 'package_number']
    search_fields = ['shipping_no', 'order__order_number', 'order_item__product__product_code']
    ordering_fields = ['shipping_date', 'created_at']
    ordering = ['-shipping_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ShippingListSerializer
        return ShippingSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(shipping_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(shipping_date__lte=date_to)
            
        # Filter by customer
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(order__customer=customer)
            
        return queryset.select_related(
            'order', 'order_item', 'order_item__product', 'order__customer'
        )
    
    @action(detail=False, methods=['get'])
    def by_order(self, request):
        """Get all shipments for a specific order"""
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response(
                {'error': 'order_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shipments = self.get_queryset().filter(order=order_id)
        serializer = self.get_serializer(shipments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_order_item(self, request):
        """Get all shipments for a specific order item with remaining quantity"""
        order_item_id = request.query_params.get('order_item_id')
        if not order_item_id:
            return Response(
                {'error': 'order_item_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order_item = SalesOrderItem.objects.get(id=order_item_id)
        except SalesOrderItem.DoesNotExist:
            return Response(
                {'error': 'Order item not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        shipments = self.get_queryset().filter(order_item=order_item_id)
        total_shipped = shipments.aggregate(total=Sum('quantity'))['total'] or 0
        remaining_quantity = order_item.quantity - total_shipped
        
        serializer = self.get_serializer(shipments, many=True)
        return Response({
            'shipments': serializer.data,
            'order_item': {
                'id': order_item.id,
                'product_code': order_item.product.product_code,
                'product_name': order_item.product.name,
                'ordered_quantity': order_item.quantity,
                'shipped_quantity': total_shipped,
                'remaining_quantity': remaining_quantity,
                'status': order_item.get_status_display()
            }
        })
    
    @action(detail=False, methods=['post'])
    def create_shipment(self, request):
        """Create a new shipment with validation"""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            shipment = serializer.save()
            
            # Update order item status to SHIPPED if fully shipped
            order_item = shipment.order_item
            total_shipped = Shipping.objects.filter(
                order_item=order_item
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            if total_shipped >= order_item.quantity:
                order_item.status = OrderItemStatus.SHIPPED
                order_item.save()
        
        return Response(
            self.get_serializer(shipment).data, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def shipping_summary(self, request):
        """Get shipping summary statistics"""
        today = timezone.now().date()
        
        # Get shipments for different time periods
        today_shipments = self.get_queryset().filter(shipping_date=today)
        this_week_start = today - timedelta(days=today.weekday())
        week_shipments = self.get_queryset().filter(
            shipping_date__gte=this_week_start,
            shipping_date__lte=today
        )
        month_shipments = self.get_queryset().filter(
            shipping_date__year=today.year,
            shipping_date__month=today.month
        )
        
        return Response({
            'today': {
                'count': today_shipments.count(),
                'total_quantity': today_shipments.aggregate(
                    total=Sum('quantity')
                )['total'] or 0,
                'packages': today_shipments.aggregate(
                    total=Sum('package_number')
                )['total'] or 0
            },
            'this_week': {
                'count': week_shipments.count(),
                'total_quantity': week_shipments.aggregate(
                    total=Sum('quantity')
                )['total'] or 0,
                'packages': week_shipments.aggregate(
                    total=Sum('package_number')
                )['total'] or 0
            },
            'this_month': {
                'count': month_shipments.count(),
                'total_quantity': month_shipments.aggregate(
                    total=Sum('quantity')
                )['total'] or 0,
                'packages': month_shipments.aggregate(
                    total=Sum('package_number')
                )['total'] or 0
            }
        })
    
    @action(detail=False, methods=['get'])
    def pending_shipments(self, request):
        """Get order items that are ready for shipment but not fully shipped"""
        ready_items = SalesOrderItem.objects.filter(
            status=OrderItemStatus.READY
        ).select_related('sales_order', 'product')
        
        pending_data = []
        for item in ready_items:
            shipped_quantity = Shipping.objects.filter(
                order_item=item
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            remaining_quantity = item.quantity - shipped_quantity
            if remaining_quantity > 0:
                pending_data.append({
                    'order_item_id': item.id,
                    'order_number': item.sales_order.order_number,
                    'customer_name': item.sales_order.customer.name,
                    'product_code': item.product.product_code,
                    'product_name': item.product.name,
                    'ordered_quantity': item.quantity,
                    'shipped_quantity': shipped_quantity,
                    'remaining_quantity': remaining_quantity,
                    'delivery_date': item.delivery_date
                })
        
        return Response({
            'pending_shipments': pending_data,
            'total_items': len(pending_data)
        })