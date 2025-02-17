from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters import rest_framework as filters
from django.utils import timezone
from django.db import models

from .models import SalesOrder, SalesOrderItem, Shipping
from .serializers import SalesOrderSerializer, SalesOrderItemSerializer, ShippingSerializer
from erp_core.permissions import IsAdminUser, HasDepartmentPermission

# Create your views here.

class SalesOrderFilter(filters.FilterSet):
    order_date_from = filters.DateFilter(field_name='order_date', lookup_expr='gte')
    order_date_to = filters.DateFilter(field_name='order_date', lookup_expr='lte')
    status = filters.CharFilter(field_name='status')
    customer = filters.CharFilter(field_name='customer__name', lookup_expr='icontains')

    class Meta:
        model = SalesOrder
        fields = ['order_date_from', 'order_date_to', 'status', 'customer']

class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.prefetch_related('items').all().select_related(
        'customer', 'approved_by'
    )
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = SalesOrderFilter
    search_fields = ['order_number', 'customer__name', 'status']
    ordering_fields = ['order_date', 'deadline_date', 'status']
    ordering = ['-order_date']

    def perform_create(self, serializer):
        # Generate order number logic here
        # You might want to implement your own order number generation logic
        year = timezone.now().year
        month = timezone.now().month
        count = SalesOrder.objects.filter(
            order_date__year=year,
            order_date__month=month
        ).count() + 1
        
        order_number = f'SO{year}{month:02d}{count:04d}'
        serializer.save(order_number=order_number)

    @swagger_auto_schema(
        operation_description="List all sales orders",
        responses={200: SalesOrderSerializer(many=True)},
        tags=['Sales Orders']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new sales order",
        request_body=SalesOrderSerializer,
        responses={201: SalesOrderSerializer()},
        tags=['Sales Orders']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a sales order",
        responses={200: SalesOrderSerializer()},
        tags=['Sales Orders']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Approve a sales order",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'approver_notes': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: SalesOrderSerializer()},
        tags=['Sales Orders']
    )
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        sales_order = self.get_object()
        if sales_order.status != 'PENDING_APPROVAL':
            return Response(
                {"detail": "Only orders in PENDING_APPROVAL status can be approved"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sales_order.status = 'APPROVED'
        sales_order.approved_by = request.user
        sales_order.save()
        
        serializer = self.get_serializer(sales_order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        sales_order = self.get_object()
        if sales_order.status in ['COMPLETED', 'CANCELLED']:
            return Response(
                {"detail": "Cannot cancel completed or already cancelled orders"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sales_order.status = 'CANCELLED'
        sales_order.save()
        
        serializer = self.get_serializer(sales_order)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        overdue_orders = self.get_queryset().filter(
            deadline_date__lt=timezone.now().date(),
            status__in=['PENDING', 'APPROVED']
        )
        serializer = self.get_serializer(overdue_orders, many=True)
        return Response(serializer.data)

class SalesOrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = SalesOrderItemSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]

    def get_queryset(self):
        order_id = self.kwargs.get('salesorder_pk')
        return SalesOrderItem.objects.filter(sales_order__id=order_id)

class ShippingFilter(filters.FilterSet):
    shipping_date_from = filters.DateFilter(field_name='shipping_date', lookup_expr='gte')
    shipping_date_to = filters.DateFilter(field_name='shipping_date', lookup_expr='lte')
    status = filters.CharFilter(field_name='status')
    carrier = filters.CharFilter(field_name='carrier')
    delivery_status = filters.CharFilter(method='filter_delivery_status')

    class Meta:
        model = Shipping
        fields = ['shipping_date_from', 'shipping_date_to', 'status', 'carrier']

    def filter_delivery_status(self, queryset, name, value):
        if value.upper() == 'ON TIME':
            return queryset.filter(
                status='DELIVERED',
                actual_delivery_date__lte=models.F('estimated_delivery_date')
            )
        elif value.upper() == 'DELAYED':
            return queryset.filter(
                status='DELIVERED',
                actual_delivery_date__gt=models.F('estimated_delivery_date')
            )
        return queryset

class ShippingViewSet(viewsets.ModelViewSet):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ShippingFilter
    search_fields = ['shipping_no', 'tracking_number', 'carrier']
    ordering_fields = ['shipping_date', 'estimated_delivery_date', 'status']
    ordering = ['-shipping_date']

    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        """Get shipping performance metrics"""
        queryset = self.get_queryset()
        
        # Calculate metrics
        total_shipments = queryset.count()
        delivered_shipments = queryset.filter(status='DELIVERED').count()
        
        # On-time delivery rate
        on_time_deliveries = queryset.filter(
            status='DELIVERED',
            actual_delivery_date__lte=models.F('estimated_delivery_date')
        ).count()
        
        on_time_rate = (on_time_deliveries / delivered_shipments * 100) if delivered_shipments > 0 else 0
        
        # Average transit time
        avg_transit_time = queryset.filter(
            status='DELIVERED',
            actual_delivery_date__isnull=False
        ).annotate(
            transit_days=models.ExpressionWrapper(
                models.F('actual_delivery_date') - models.F('shipping_date'),
                output_field=models.DurationField()
            )
        ).aggregate(avg_days=models.Avg('transit_days'))['avg_days']
        
        # Status breakdown
        status_breakdown = queryset.values('status').annotate(
            count=models.Count('id')
        ).order_by('status')
        
        return Response({
            'total_shipments': total_shipments,
            'delivered_shipments': delivered_shipments,
            'on_time_delivery_rate': round(on_time_rate, 2),
            'average_transit_time_days': round(avg_transit_time.days if avg_transit_time else 0, 2),
            'status_breakdown': status_breakdown
        })

    @action(detail=False, methods=['get'])
    def order_shipments(self, request):
        """Get all shipments for a specific order with performance metrics"""
        order_id = request.query_params.get('order_id')
        if not order_id:
            return Response(
                {"error": "order_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shipments = self.get_queryset().filter(order_id=order_id)
        serializer = self.get_serializer(shipments, many=True)
        
        # Calculate order-specific metrics
        total_shipments = shipments.count()
        delivered_shipments = shipments.filter(status='DELIVERED').count()
        on_time_deliveries = shipments.filter(
            status='DELIVERED',
            actual_delivery_date__lte=models.F('estimated_delivery_date')
        ).count()
        
        return Response({
            "shipments": serializer.data,
            "metrics": {
                "total_shipments": total_shipments,
                "delivered_shipments": delivered_shipments,
                "on_time_deliveries": on_time_deliveries,
                "total_amount": sum(shipment.shipping_amount for shipment in shipments)
            }
        })
