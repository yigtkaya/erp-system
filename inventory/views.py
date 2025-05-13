from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, RawMaterial, StockTransaction
from .serializers import ProductSerializer, RawMaterialSerializer
from .stock_manager import StockManager


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product_type', 'inventory_category', 'is_active']
    search_fields = ['product_code', 'product_name', 'description']
    ordering_fields = ['product_code', 'product_name', 'current_stock', 'created_at']
    
    @action(detail=True, methods=['get'])
    def stock_history(self, request, pk=None):
        product = self.get_object()
        history = StockManager.get_product_stock_history(product)
        # Create a simplified response for history
        data = [{
            'date': transaction.transaction_date,
            'type': transaction.get_transaction_type_display(),
            'quantity': transaction.quantity,
            'category': transaction.category.name,
            'reference': transaction.reference,
            'notes': transaction.notes
        } for transaction in history]
        return Response(data)


class RawMaterialViewSet(viewsets.ModelViewSet):
    queryset = RawMaterial.objects.all()
    serializer_class = RawMaterialSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['material_type', 'inventory_category', 'is_active']
    search_fields = ['material_code', 'material_name', 'description']
    ordering_fields = ['material_code', 'material_name', 'current_stock', 'created_at']
    
    @action(detail=True, methods=['get'])
    def stock_history(self, request, pk=None):
        raw_material = self.get_object()
        history = StockManager.get_raw_material_stock_history(raw_material)
        # Create a simplified response for history
        data = [{
            'date': transaction.transaction_date,
            'type': transaction.get_transaction_type_display(),
            'quantity': transaction.quantity,
            'category': transaction.category.name,
            'reference': transaction.reference,
            'notes': transaction.notes
        } for transaction in history]
        return Response(data)
