from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters import rest_framework as filters
from django.utils import timezone
from django.db import models
from rest_framework.exceptions import ValidationError

from .models import SalesOrder, SalesOrderItem, Shipping
from .serializers import (
    SalesOrderSerializer, SalesOrderItemSerializer,
    ShippingSerializer
)
from erp_core.permissions import IsAdminUser, HasDepartmentPermission

# Create your views here.

class SalesOrderFilter(filters.FilterSet):
    order_date_from = filters.DateFilter(field_name='order_date', lookup_expr='gte')
    order_date_to = filters.DateFilter(field_name='order_date', lookup_expr='lte')
    status = filters.ChoiceFilter(choices=SalesOrder.STATUS_CHOICES)
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
    lookup_field = 'id'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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
    queryset = SalesOrderItem.objects.all()
    serializer_class = SalesOrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        order_id = self.kwargs.get('salesorder_pk')
        return SalesOrderItem.objects.filter(sales_order__id=order_id)

class ShippingViewSet(viewsets.ModelViewSet):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'shipping_no'

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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

class CreateShipmentView(generics.CreateAPIView):
    serializer_class = ShippingSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        order = get_object_or_404(SalesOrder, order_number=kwargs['order_number'])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(order=order, created_by=self.request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class UpdateShipmentStatusView(generics.UpdateAPIView):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'shipping_no'

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
