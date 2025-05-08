# sales/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from .models import (
    Currency, SalesOrder, SalesOrderItem, SalesQuotation,
    SalesQuotationItem, CustomerPriceList
)
from .serializers import (
    CurrencySerializer, SalesOrderSerializer, SalesOrderItemSerializer,
    SalesQuotationSerializer, SalesQuotationItemSerializer,
    CustomerPriceListSerializer
)
from core.permissions import HasRolePermission


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['is_active']
    search_fields = ['code', 'name']


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['status', 'customer', 'salesperson']
    search_fields = ['order_number', 'customer__name', 'customer_po_number']
    ordering_fields = ['order_date', 'delivery_date', 'created_at']
    ordering = ['-order_date']
    
    def perform_create(self, serializer):
        serializer.save(
            salesperson=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        
        if order.status != 'DRAFT':
            return Response(
                {'error': 'Only draft orders can be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'CONFIRMED'
        order.save()
        
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
        
        if order.status in ['DELIVERED', 'CANCELLED']:
            return Response(
                {'error': 'Cannot cancel delivered or already cancelled orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'CANCELLED'
        order.save()
        
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
            
            # Update order totals
            order.update_totals()
            
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
                order_date=timezone.now().date(),
                delivery_date=timezone.now().date() + timezone.timedelta(days=30),
                status='CONFIRMED',
                currency=quotation.currency,
                exchange_rate=quotation.exchange_rate,
                payment_terms=quotation.payment_terms,
                salesperson=request.user,
                shipping_address=quotation.customer.address,
                billing_address=quotation.customer.address,
                notes=f"Created from quotation {quotation.quotation_number}",
                created_by=request.user
            )
            
            # Copy quotation items to order items
            for quote_item in quotation.items.all():
                SalesOrderItem.objects.create(
                    sales_order=order,
                    product=quote_item.product,
                    quantity=quote_item.quantity,
                    unit_price=quote_item.unit_price,
                    discount_percentage=quote_item.discount_percentage,
                    tax_percentage=quote_item.tax_percentage,
                    delivery_date=order.delivery_date
                )
            
            # Update order totals
            order.update_totals()
            
            # Link quotation to order
            quotation.converted_to_order = order
            quotation.save()
            
            return Response(
                SalesOrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )


class CustomerPriceListViewSet(viewsets.ModelViewSet):
    queryset = CustomerPriceList.objects.all()
    serializer_class = CustomerPriceListSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['customer', 'product', 'is_active']
    search_fields = ['customer__name', 'product__product_code']
    ordering = ['customer', 'product']
    
    @action(detail=False, methods=['get'])
    def get_price(self, request):
        """Get price for a customer and product"""
        customer_id = request.query_params.get('customer_id')
        product_id = request.query_params.get('product_id')
        quantity = request.query_params.get('quantity', 1)
        
        if not customer_id or not product_id:
            return Response(
                {'error': 'customer_id and product_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        today = timezone.now().date()
        price_list = CustomerPriceList.objects.filter(
            customer_id=customer_id,
            product_id=product_id,
            is_active=True,
            valid_from__lte=today
        ).filter(
            Q(valid_until__gte=today) | Q(valid_until__isnull=True)
        ).filter(
            minimum_quantity__lte=quantity
        ).order_by('-minimum_quantity').first()
        
        if price_list:
            serializer = self.get_serializer(price_list)
            return Response(serializer.data)
        else:
            return Response(
                {'error': 'No valid price found'},
                status=status.HTTP_404_NOT_FOUND
            )