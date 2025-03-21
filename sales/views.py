from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters import rest_framework as filters
from django.utils import timezone
from django.db import models, transaction
from rest_framework.exceptions import ValidationError

from .models import SalesOrder, SalesOrderItem, Shipping
from .serializers import (
    SalesOrderSerializer, SalesOrderItemSerializer,
    ShippingSerializer, BatchSalesOrderItemUpdateSerializer,
    BatchSalesOrderItemCreateSerializer, BatchShippingUpdateSerializer,
    BatchOrderShipmentUpdateSerializer
)
from erp_core.permissions import IsAdminUser, HasDepartmentPermission

# Create your views here.

class SalesOrderFilter(filters.FilterSet):
    created_at_from = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = filters.DateFilter(field_name='created_at', lookup_expr='lte')
    status = filters.ChoiceFilter(choices=SalesOrder.STATUS_CHOICES)
    customer = filters.CharFilter(field_name='customer__name', lookup_expr='icontains')

    class Meta:
        model = SalesOrder
        fields = ['created_at_from', 'created_at_to', 'status', 'customer']

class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.prefetch_related('items').all().select_related(
        'customer', 'approved_by'
    )
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = SalesOrderFilter
    search_fields = ['order_number', 'customer__name', 'status']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        with transaction.atomic():
            order = serializer.save(created_by=self.request.user)
            # Validate item dates after creation
            for item in order.items.all():
                item.full_clean()

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
        if sales_order.status != 'OPEN':
            return Response(
                {"detail": "Only OPEN orders can be approved"},
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
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']  # Explicitly allow PATCH

    def get_queryset(self):
        order_id = self.kwargs.get('order_pk')
        if order_id:
            return SalesOrderItem.objects.filter(sales_order_id=order_id)
        return SalesOrderItem.objects.none()

    def update(self, request, *args, **kwargs):
        # Get the parent order first
        order_id = self.kwargs.get('order_pk')
        order = get_object_or_404(SalesOrder, pk=order_id)
        
        # Get the specific item
        instance = self.get_object()
        partial = kwargs.pop('partial', False)
        
        # Prevent updates if order is closed
        if order.status == 'CLOSED':
            return Response(
                {"detail": "Cannot update items in a closed order"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        order_id = self.kwargs.get('order_pk')
        order = get_object_or_404(SalesOrder, pk=order_id)
        instance = self.get_object()
        
        if order.status == 'CLOSED':
            return Response(
                {"detail": "Cannot delete items from a closed order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        order.update_order_status()  # Update parent order status
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        # Ensure the item belongs to the parent order
        self.get_object()  # Will trigger 404 if not found in parent order
        return super().retrieve(request, *args, **kwargs)
        
    @swagger_auto_schema(
        operation_description="Update multiple sales order items in a single request",
        request_body=BatchSalesOrderItemUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Items updated successfully",
                schema=SalesOrderItemSerializer(many=True)
            ),
            400: "Bad request if validation fails or order is closed",
            404: "Order not found"
        },
        tags=['Sales Order Items']
    )
    @action(detail=False, methods=['patch'], url_path='batch-update')
    def batch_update(self, request, order_pk=None):
        """
        Update multiple sales order items in a single request.
        """
        # Get the parent order
        order = get_object_or_404(SalesOrder, pk=order_pk)
        
        # Prevent updates if order is closed
        if order.status == 'CLOSED':
            return Response(
                {"detail": "Cannot update items in a closed order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use the batch update serializer
        serializer = BatchSalesOrderItemUpdateSerializer(
            instance=order,
            data=request.data,
            context={'request': request, 'order_id': order_pk}
        )
        
        serializer.is_valid(raise_exception=True)
        result = serializer.update(order, serializer.validated_data)
        
        # Return the updated items
        response_serializer = SalesOrderItemSerializer(
            result['updated_items'], 
            many=True,
            context={'request': request}
        )
        
        return Response(response_serializer.data)
        
    @swagger_auto_schema(
        operation_description="Create multiple sales order items in a single request",
        request_body=BatchSalesOrderItemCreateSerializer,
        responses={
            201: openapi.Response(
                description="Items created successfully",
                schema=SalesOrderItemSerializer(many=True)
            ),
            400: "Bad request if validation fails or order is closed",
            404: "Order not found"
        },
        tags=['Sales Order Items']
    )
    @action(detail=False, methods=['post'], url_path='batch-create')
    def batch_create(self, request, order_pk=None):
        """
        Create multiple sales order items in a single request.
        """
        # Get the parent order
        order = get_object_or_404(SalesOrder, pk=order_pk)
        
        # Prevent updates if order is closed
        if order.status == 'CLOSED':
            return Response(
                {"detail": "Cannot add items to a closed order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use the batch create serializer
        serializer = BatchSalesOrderItemCreateSerializer(
            data=request.data,
            context={'request': request, 'order_id': order_pk}
        )
        
        serializer.is_valid(raise_exception=True)
        result = serializer.create(serializer.validated_data)
        
        # Return the created items
        response_serializer = SalesOrderItemSerializer(
            result['created_items'], 
            many=True,
            context={'request': request}
        )
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class ShippingViewSet(viewsets.ModelViewSet):
    queryset = Shipping.objects.all()
    serializer_class = ShippingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'shipping_no'
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        """
        Get the queryset filtered by order if order_pk is provided
        """
        queryset = super().get_queryset()
        order_pk = self.kwargs.get('order_pk')
        if order_pk is not None:
            queryset = queryset.filter(order_id=order_pk)
        return queryset

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        if 'order_pk' in self.kwargs:
            context['order_id'] = self.kwargs['order_pk']
        return context

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(created_by=self.request.user)
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

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
                "on_time_deliveries": on_time_deliveries
            }
        })

    @swagger_auto_schema(
        operation_description="Batch update shipments for a specific sales order",
        request_body=BatchOrderShipmentUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Shipments updated successfully",
                schema=ShippingSerializer(many=True)
            ),
            400: "Validation error",
            404: "Order not found"
        },
        tags=['Shipments']
    )
    @action(detail=False, methods=['patch'], url_path='batch-update')
    def batch_update(self, request, order_pk=None):
        """
        Batch update shipments for a specific sales order
        """
        try:
            if not order_pk:
                return Response(
                    {"detail": "Order ID is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                order = SalesOrder.objects.get(pk=order_pk)
            except SalesOrder.DoesNotExist:
                return Response(
                    {"detail": "Order not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = BatchOrderShipmentUpdateSerializer(
                data=request.data,
                context={'order_id': order.id, 'request': request}
            )

            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                updated_shipments = serializer.update(None, serializer.validated_data)
                response_serializer = ShippingSerializer(
                    updated_shipments, 
                    many=True,
                    context=self.get_serializer_context()
                )
                return Response(response_serializer.data)

        except ValidationError as e:
            return Response(
                {"detail": str(e) if str(e) else "Validation error occurred"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """
        Delete a shipping record if it's allowed
        """
        shipping = self.get_object()
        
        # Check if the order is closed
        if shipping.order.status == 'CLOSED':
            return Response(
                {"detail": "Cannot delete shipments from a closed order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform the deletion
        shipping.delete()
        
        # Update the order item's fulfilled quantity
        shipping.order_item.update_fulfilled_quantity()
        shipping.order_item.save()
        
        # Update the order status
        shipping.order.update_order_status()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class SalesOrderByNumberView(generics.RetrieveAPIView):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'
    lookup_url_kwarg = 'order_number'

class CreateShipmentView(generics.CreateAPIView):
    serializer_class = ShippingSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        order = get_object_or_404(SalesOrder, id=kwargs['order_id'])
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
