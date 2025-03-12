from django.shortcuts import render
from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    InventoryCategory, UnitOfMeasure, Product,
    TechnicalDrawing, RawMaterial, InventoryTransaction, UnitOfMeasure,
    Tool, Holder, Fixture, ControlGauge
)
from .serializers import (
    InventoryCategorySerializer, UnitOfMeasureSerializer,
    ProductSerializer, TechnicalDrawingDetailSerializer,
    TechnicalDrawingListSerializer, RawMaterialSerializer, 
    InventoryTransactionSerializer, UnitOfMeasureSerializer,
    ToolSerializer, HolderSerializer, FixtureSerializer, ControlGaugeSerializer
)

class UnitOfMeasureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    permission_classes = [IsAuthenticated]

class InventoryCategoryViewSet(viewsets.ModelViewSet):
    queryset = InventoryCategory.objects.all()
    serializer_class = InventoryCategorySerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all inventory categories",
        responses={200: InventoryCategorySerializer(many=True)},
        tags=['Inventory Categories']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new inventory category",
        request_body=InventoryCategorySerializer,
        responses={201: InventoryCategorySerializer()},
        tags=['Inventory Categories']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related('inventory_category').prefetch_related('technicaldrawing_set')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply filters
        category = self.request.query_params.get('category', None)
        product_type = self.request.query_params.get('product_type', None)
        product_code = self.request.query_params.get('product_code', None)
        product_name = self.request.query_params.get('product_name', None)

        # Dimension range filters
        width_min = self.request.query_params.get('width_min', None)
        width_max = self.request.query_params.get('width_max', None)
        height_min = self.request.query_params.get('height_min', None)
        height_max = self.request.query_params.get('height_max', None)
        thickness_min = self.request.query_params.get('thickness_min', None)
        thickness_max = self.request.query_params.get('thickness_max', None)
        diameter_min = self.request.query_params.get('diameter_min', None)
        diameter_max = self.request.query_params.get('diameter_max', None)

        try:
            if category:
                queryset = queryset.filter(inventory_category__name=category)
            if product_type:
                queryset = queryset.filter(product_type=product_type)
            if product_code:
                queryset = queryset.filter(product_code__icontains=product_code)
            if product_name:
                queryset = queryset.filter(product_name__icontains=product_name)
            
            # Apply dimension range filters
            if width_min is not None:
                queryset = queryset.filter(width__gte=float(width_min))
            if width_max is not None:
                queryset = queryset.filter(width__lte=float(width_max))
            
            if height_min is not None:
                queryset = queryset.filter(height__gte=float(height_min))
            if height_max is not None:
                queryset = queryset.filter(height__lte=float(height_max))
            
            if thickness_min is not None:
                queryset = queryset.filter(thickness__gte=float(thickness_min))
            if thickness_max is not None:
                queryset = queryset.filter(thickness__lte=float(thickness_max))
            
            if diameter_min is not None:
                queryset = queryset.filter(diameter_mm__gte=float(diameter_min))
            if diameter_max is not None:
                queryset = queryset.filter(diameter_mm__lte=float(diameter_max))

        except ValueError as e:
            raise ValidationError(f"Invalid numeric value in dimension filters: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Invalid filter parameters: {str(e)}")

        return queryset

    @swagger_auto_schema(
        operation_description="List all products with optional filters, including associated technical drawings",
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Filter by inventory category (e.g. HAMMADDE, HURDA, KARANTINA)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'product_type',
                openapi.IN_QUERY,
                description="Filter by product type (e.g. STANDARD_PART)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'product_code',
                openapi.IN_QUERY,
                description="Filter by product code (exact match)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'product_name',
                openapi.IN_QUERY,
                description="Filter by product name (case-insensitive partial match)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            # Dimension range filter parameters
            openapi.Parameter(
                'width_min',
                openapi.IN_QUERY,
                description="Minimum width value",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'width_max',
                openapi.IN_QUERY,
                description="Maximum width value",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'height_min',
                openapi.IN_QUERY,
                description="Minimum height value",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'height_max',
                openapi.IN_QUERY,
                description="Maximum height value",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'thickness_min',
                openapi.IN_QUERY,
                description="Minimum thickness value",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'thickness_max',
                openapi.IN_QUERY,
                description="Maximum thickness value",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'diameter_min',
                openapi.IN_QUERY,
                description="Minimum diameter value (in mm)",
                type=openapi.TYPE_NUMBER,
                required=False
            ),
            openapi.Parameter(
                'diameter_max',
                openapi.IN_QUERY,
                description="Maximum diameter value (in mm)",
                type=openapi.TYPE_NUMBER,
                required=False
            )
        ],
        responses={
            200: ProductSerializer(many=True),
            400: "Invalid filter parameters",
            500: "Internal server error"
        },
        tags=['Products']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new product",
        request_body=ProductSerializer,
        responses={201: ProductSerializer()},
        tags=['Products']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        method='post',
        operation_description="Transfer product between categories",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['to_category'],
            properties={
                'to_category': openapi.Schema(type=openapi.TYPE_INTEGER),
                'notes': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            200: openapi.Response(
                description="Product transferred successfully",
                schema=ProductSerializer()
            ),
            400: "Invalid category transfer"
        },
        tags=['Products']
    )
    @action(detail=True, methods=['post'])
    def transfer_category(self, request, pk=None):
        product = self.get_object()
        to_category_id = request.data.get('to_category')
        notes = request.data.get('notes', '')

        try:
            to_category = InventoryCategory.objects.get(pk=to_category_id)
            transaction = InventoryTransaction.objects.create(
                product=product,
                quantity_change=0,
                transaction_type='TRANSFER',
                performed_by=request.user,
                notes=notes,
                from_category=product.inventory_category,
                to_category=to_category
            )
            product.inventory_category = to_category
            product.save()
            return Response(self.get_serializer(product).data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class TechnicalDrawingViewSet(viewsets.ModelViewSet):
    queryset = TechnicalDrawing.objects.all().select_related('product', 'approved_by')
    serializer_class = TechnicalDrawingDetailSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_serializer_class(self):
        if self.action == 'list':
            return TechnicalDrawingListSerializer
        return TechnicalDrawingDetailSerializer

    @swagger_auto_schema(
        operation_description="List all technical drawings with optional filters",
        manual_parameters=[
            openapi.Parameter(
                'product',
                openapi.IN_QUERY,
                description="Filter by product ID",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'is_current',
                openapi.IN_QUERY,
                description="Filter by current version status",
                type=openapi.TYPE_BOOLEAN,
                required=False
            )
        ],
        responses={
            200: TechnicalDrawingListSerializer(many=True),
            400: "Invalid filter parameters",
            500: "Internal server error"
        },
        tags=['Technical Drawings']
    )
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            
            # Apply filters
            product_id = request.query_params.get('product', None)
            is_current = request.query_params.get('is_current', None)

            if product_id:
                queryset = queryset.filter(product_id=product_id)
            if is_current is not None:
                is_current = is_current.lower() == 'true'
                queryset = queryset.filter(is_current=is_current)

            # Apply pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': 'Internal server error occurred', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Create a new technical drawing",
        request_body=TechnicalDrawingDetailSerializer,
        responses={201: TechnicalDrawingDetailSerializer()},
        tags=['Technical Drawings']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    @swagger_auto_schema(
        operation_description="Update a technical drawing",
        request_body=TechnicalDrawingDetailSerializer,
        responses={200: TechnicalDrawingDetailSerializer()},
        tags=['Technical Drawings']
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class InventoryTransactionViewSet(viewsets.ModelViewSet):
    queryset = InventoryTransaction.objects.all()
    serializer_class = InventoryTransactionSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all inventory transactions",
        manual_parameters=[
            openapi.Parameter(
                'transaction_type',
                openapi.IN_QUERY,
                description="Filter by transaction type",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'product',
                openapi.IN_QUERY,
                description="Filter by product ID",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'material',
                openapi.IN_QUERY,
                description="Filter by material ID",
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={200: InventoryTransactionSerializer(many=True)},
        tags=['Inventory Transactions']
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        transaction_type = request.query_params.get('transaction_type', None)
        product_id = request.query_params.get('product', None)
        material_id = request.query_params.get('material', None)

        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if material_id:
            queryset = queryset.filter(material_id=material_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new inventory transaction",
        request_body=InventoryTransactionSerializer,
        responses={
            201: InventoryTransactionSerializer(),
            400: "Invalid transaction data"
        },
        tags=['Inventory Transactions']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(performed_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class RawMaterialViewSet(viewsets.ModelViewSet):
    queryset = RawMaterial.objects.all()
    serializer_class = RawMaterialSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all raw materials with optional filters",
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description="Filter by inventory category (e.g. HAMMADDE, HURDA, KARANTINA)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'material_code',
                openapi.IN_QUERY,
                description="Filter by material code (exact match)",
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'material_name',
                openapi.IN_QUERY,
                description="Filter by material name (case-insensitive partial match)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={200: RawMaterialSerializer(many=True)},
        tags=['Raw Materials']
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Apply filters
        category = request.query_params.get('category', None)
        material_code = request.query_params.get('material_code', None)
        material_name = request.query_params.get('material_name', None)

        if category:
            queryset = queryset.filter(inventory_category__name=category)
        if material_code:
            queryset = queryset.filter(material_code__icontains=material_code)
        if material_name:
            queryset = queryset.filter(material_name__icontains=material_name)

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new raw material",
        request_body=RawMaterialSerializer,
        responses={201: RawMaterialSerializer()},
        tags=['Raw Materials']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

class MaterialTypeChoicesAPIView(APIView):
    """
    API view to get available material type choices.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Get the field choices from the RawMaterial model.
        choices = RawMaterial._meta.get_field('material_type').choices
        return Response({
            'choices': [{'value': value, 'display': display} for value, display in choices]
        })

class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    lookup_field = 'stock_code'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tool_type', 'status', 'tool_material']
    search_fields = ['stock_code', 'product_code', 'description']
    ordering_fields = ['stock_code', 'updated_at', 'tool_type']
    ordering = ['stock_code']

    def get_queryset(self):
        queryset = super().get_queryset()
        row = self.request.query_params.get('row', None)
        column = self.request.query_params.get('column', None)
        
        if row is not None and column is not None:
            queryset = queryset.filter(row=row, column=column)
        return queryset

class HolderViewSet(viewsets.ModelViewSet):
    queryset = Holder.objects.all()
    serializer_class = HolderSerializer
    lookup_field = 'stock_code'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['holder_type', 'status', 'water_cooling', 'distance_cooling']
    search_fields = ['stock_code', 'product_code', 'description']
    ordering_fields = ['stock_code', 'updated_at', 'holder_type']
    ordering = ['stock_code']

    def get_queryset(self):
        queryset = super().get_queryset()
        row = self.request.query_params.get('row', None)
        column = self.request.query_params.get('column', None)
        
        if row is not None and column is not None:
            queryset = queryset.filter(row=row, column=column)
        return queryset

class FixtureViewSet(viewsets.ModelViewSet):
    queryset = Fixture.objects.all()
    serializer_class = FixtureSerializer
    permission_classes = [IsAuthenticated]

class ControlGaugeViewSet(viewsets.ModelViewSet):
    queryset = ControlGauge.objects.all()
    serializer_class = ControlGaugeSerializer
    permission_classes = [IsAuthenticated]
