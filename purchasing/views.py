# purchasing/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone
from .models import (
    Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseRequisition,
    PurchaseRequisitionItem, GoodsReceipt, GoodsReceiptItem,
    SupplierPriceList
)
from .serializers import (
    SupplierSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer,
    PurchaseRequisitionSerializer, PurchaseRequisitionItemSerializer,
    GoodsReceiptSerializer, GoodsReceiptItemSerializer,
    SupplierPriceListSerializer
)
from core.permissions import HasRolePermission


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['is_active', 'country']
    search_fields = ['code', 'name', 'contact_person']
    ordering_fields = ['code', 'name', 'rating']
    ordering = ['code']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['status', 'supplier', 'buyer']
    search_fields = ['po_number', 'supplier__name']
    ordering_fields = ['order_date', 'expected_delivery_date', 'created_at']
    ordering = ['-order_date']
    
    def perform_create(self, serializer):
        serializer.save(
            buyer=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        po = self.get_object()
        
        if po.status != 'REQUESTED':
            return Response(
                {'error': 'Only requested POs can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        po.status = 'APPROVED'
        po.approved_by = request.user
        po.approval_date = timezone.now()
        po.save()
        
        serializer = self.get_serializer(po)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_to_supplier(self, request, pk=None):
        po = self.get_object()
        
        if po.status != 'APPROVED':
            return Response(
                {'error': 'Only approved POs can be sent to supplier'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        po.status = 'SENT'
        po.save()
        
        # TODO: Implement actual email sending to supplier
        
        serializer = self.get_serializer(po)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_with_items(self, request):
        """Create PO with items in a single transaction"""
        with transaction.atomic():
            items_data = request.data.pop('items', [])
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            po = serializer.save(
                buyer=request.user,
                created_by=request.user
            )
            
            # Create PO items
            for item_data in items_data:
                item_data['purchase_order'] = po.id
                item_serializer = PurchaseOrderItemSerializer(data=item_data)
                item_serializer.is_valid(raise_exception=True)
                item_serializer.save()
            
            # Update PO totals
            po.update_totals()
            
            return Response(
                self.get_serializer(po).data,
                status=status.HTTP_201_CREATED
            )


class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.all()
    serializer_class = PurchaseRequisitionSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['status', 'requested_by', 'department']
    search_fields = ['requisition_number', 'requested_by__username']
    ordering_fields = ['request_date', 'required_date', 'created_at']
    ordering = ['-request_date']
    
    def perform_create(self, serializer):
        serializer.save(
            requested_by=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        requisition = self.get_object()
        
        if requisition.status != 'SUBMITTED':
            return Response(
                {'error': 'Only submitted requisitions can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        requisition.status = 'APPROVED'
        requisition.approved_by = request.user
        requisition.approval_date = timezone.now()
        requisition.save()
        
        serializer = self.get_serializer(requisition)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def convert_to_po(self, request, pk=None):
        requisition = self.get_object()
        
        if requisition.status != 'APPROVED':
            return Response(
                {'error': 'Only approved requisitions can be converted to PO'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Group items by supplier
        supplier_items = {}
        for item in requisition.items.all():
            if item.preferred_supplier:
                supplier_id = item.preferred_supplier.id
                if supplier_id not in supplier_items:
                    supplier_items[supplier_id] = []
                supplier_items[supplier_id].append(item)
        
        created_pos = []
        
        with transaction.atomic():
            for supplier_id, items in supplier_items.items():
                supplier = Supplier.objects.get(id=supplier_id)
                
                # Create PO
                po = PurchaseOrder.objects.create(
                    supplier=supplier,
                    order_date=timezone.now().date(),
                    expected_delivery_date=requisition.required_date,
                    status='DRAFT',
                    buyer=request.user,
                    shipping_address='Company Address',  # TODO: Get from settings
                    billing_address='Company Address',
                    payment_terms=supplier.payment_terms or 'NET_30',
                    created_by=request.user
                )
                
                # Create PO items
                for req_item in items:
                    PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        product=req_item.product,
                        quantity_ordered=req_item.quantity,
                        unit_price=req_item.estimated_price or 0,
                        expected_delivery_date=requisition.required_date
                    )
                
                po.update_totals()
                created_pos.append(po)
            
            requisition.status = 'CONVERTED'
            requisition.save()
        
        return Response({
            'created_purchase_orders': [po.po_number for po in created_pos]
        })


class GoodsReceiptViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceipt.objects.all()
    serializer_class = GoodsReceiptSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['purchase_order', 'received_by']
    search_fields = ['receipt_number', 'purchase_order__po_number']
    ordering = ['-receipt_date']
    
    def perform_create(self, serializer):
        serializer.save(
            received_by=self.request.user,
            created_by=self.request.user
        )
    
    @action(detail=False, methods=['post'])
    def create_with_items(self, request):
        """Create Goods Receipt with items in a single transaction"""
        with transaction.atomic():
            items_data = request.data.pop('items', [])
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            gr = serializer.save(
                received_by=request.user,
                created_by=request.user
            )
            
            # Create GR items
            for item_data in items_data:
                item_data['goods_receipt'] = gr.id
                item_serializer = GoodsReceiptItemSerializer(data=item_data)
                item_serializer.is_valid(raise_exception=True)
                item_serializer.save()
            
            # Update related PO and inventory
            # TODO: Update PO delivery status and inventory levels
            
            return Response(
                self.get_serializer(gr).data,
                status=status.HTTP_201_CREATED
            )


class SupplierPriceListViewSet(viewsets.ModelViewSet):
    queryset = SupplierPriceList.objects.all()
    serializer_class = SupplierPriceListSerializer
    permission_classes = [IsAuthenticated, HasRolePermission]
    filterset_fields = ['supplier', 'product', 'is_active']
    search_fields = ['supplier__name', 'product__product_code']
    ordering = ['supplier', 'product']