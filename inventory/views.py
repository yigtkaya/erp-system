from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Product, RawMaterial, StockTransaction,
    Tool, ToolUsage, Holder, Fixture, ControlGauge
)
from .serializers import (
    ProductSerializer, RawMaterialSerializer,
    ToolSerializer, ToolUsageSerializer, HolderSerializer, FixtureSerializer, ControlGaugeSerializer
)
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


class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tool_type', 'status', 'supplier_name']
    search_fields = ['stock_code', 'supplier_name', 'product_code', 'tool_insert_code', 'description']
    ordering_fields = ['stock_code', 'supplier_name', 'tool_type', 'status', 'quantity']


class ToolUsageViewSet(viewsets.ModelViewSet):
    queryset = ToolUsage.objects.all()
    serializer_class = ToolUsageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tool__stock_code', 'issued_by', 'returned_to', 'condition_before', 'condition_after']
    search_fields = ['tool__stock_code', 'notes', 'issued_by__username', 'returned_to__username']
    ordering_fields = ['issued_date', 'returned_date', 'tool__stock_code']


class HolderViewSet(viewsets.ModelViewSet):
    queryset = Holder.objects.all()
    serializer_class = HolderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['holder_type', 'status', 'supplier_name', 'water_cooling', 'distance_cooling']
    search_fields = ['stock_code', 'supplier_name', 'product_code', 'description']
    ordering_fields = ['stock_code', 'supplier_name', 'holder_type', 'status']


class FixtureViewSet(viewsets.ModelViewSet):
    queryset = Fixture.objects.all()
    serializer_class = FixtureSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name', 'status']


class ControlGaugeViewSet(viewsets.ModelViewSet):
    queryset = ControlGauge.objects.all()
    serializer_class = ControlGaugeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'calibration_per_year', 'brand', 'stock_type']
    search_fields = ['stock_code', 'stock_name', 'serial_number', 'brand', 'model', 'certificate_no', 'current_location']
    ordering_fields = ['stock_code', 'stock_name', 'status', 'upcoming_calibration_date']
