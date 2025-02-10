from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Supplier, PurchaseOrder, PurchaseOrderItem
from .serializers import SupplierSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer
from django.db import models

# Create your views here.

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filterset_fields = ['name', 'code']
    search_fields = ['name', 'code', 'contact_email']

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filterset_fields = ['status', 'supplier']
    search_fields = ['order_number', 'supplier__name']

    @action(detail=True, methods=['post'])
    def receive_items(self, request, pk=None):
        purchase_order = self.get_object()
        items_data = request.data.get('items', [])
        
        for item_data in items_data:
            try:
                item = purchase_order.items.get(id=item_data['id'])
                received_qty = item_data.get('received_quantity', 0)
                if received_qty + item.received_quantity <= item.quantity:
                    item.received_quantity += received_qty
                    item.save()
                else:
                    return Response(
                        {'error': f'Received quantity exceeds ordered quantity for item {item.id}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except PurchaseOrderItem.DoesNotExist:
                return Response(
                    {'error': f'Item {item_data["id"]} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Update PO status
        total_items = purchase_order.items.count()
        completed_items = purchase_order.items.filter(received_quantity=models.F('quantity')).count()
        partial_items = purchase_order.items.filter(received_quantity__gt=0).count()
        
        if completed_items == total_items:
            purchase_order.status = 'COMPLETED'
        elif partial_items > 0:
            purchase_order.status = 'PART_RECEIVED'
        purchase_order.save()
        
        return Response(PurchaseOrderSerializer(purchase_order).data)
