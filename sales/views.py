from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import SalesOrder, SalesOrderItem
from .serializers import SalesOrderSerializer, SalesOrderItemSerializer
from erp_core.permissions import IsAdminUser, HasDepartmentPermission

# Create your views here.

class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.prefetch_related('items').order_by('-order_date')
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer', 'status']
    search_fields = ['order_number', 'customer__name']
    
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
        if not request.user.has_perm('sales.approve_salesorder'):
            return Response(
                {'error': 'Missing approval permission'}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        sales_order.approved_by = request.user
        sales_order.status = 'APPROVED'
        sales_order.save()
        return Response(self.get_serializer(sales_order).data)

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
