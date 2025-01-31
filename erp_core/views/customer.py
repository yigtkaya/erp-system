from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from erp_core.models import Customer
from erp_core.serializers import CustomerSerializer
from erp_core.permissions import HasDepartmentPermission
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated, HasDepartmentPermission]
    search_fields = ['code', 'name']
    ordering_fields = ['created_at', 'modified_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)

    @swagger_auto_schema(
        operation_description="List all customers",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search by customer code or name",
                type=openapi.TYPE_STRING
            )
        ],
        responses={200: CustomerSerializer(many=True)},
        tags=['Customers']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new customer",
        request_body=CustomerSerializer,
        responses={201: CustomerSerializer()},
        tags=['Customers']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve customer details",
        responses={200: CustomerSerializer()},
        tags=['Customers']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a customer",
        request_body=CustomerSerializer,
        responses={200: CustomerSerializer()},
        tags=['Customers']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a customer",
        responses={204: 'No content'},
        tags=['Customers']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs) 