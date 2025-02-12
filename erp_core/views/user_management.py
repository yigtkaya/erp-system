from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from erp_core.models import User, UserProfile
from erp_core.serializers import UserSerializer
from erp_core.permissions import IsAdminUser

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users in the system.
    Only administrators can access these endpoints.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    search_fields = ['username', 'email', 'profile__employee_id']
    ordering_fields = ['created_at', 'username', 'email']
    ordering = ['-created_at']

    @swagger_auto_schema(
        operation_description="List all users",
        manual_parameters=[
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description="Search by username, email, or employee ID",
                type=openapi.TYPE_STRING
            )
        ],
        responses={200: UserSerializer(many=True)},
        tags=['User Management']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new user",
        request_body=UserSerializer,
        responses={201: UserSerializer()},
        tags=['User Management']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve user details",
        responses={200: UserSerializer()},
        tags=['User Management']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update user details",
        request_body=UserSerializer,
        responses={200: UserSerializer()},
        tags=['User Management']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update user details",
        request_body=UserSerializer,
        responses={200: UserSerializer()},
        tags=['User Management']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a user",
        responses={204: "No content"},
        tags=['User Management']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        method='post',
        operation_description="Toggle user active status",
        responses={
            200: openapi.Response(
                description="User status updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        },
        tags=['User Management']
    )
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        status_text = "activated" if user.is_active else "deactivated"
        return Response({
            'status': 'success',
            'message': f'User {user.username} has been {status_text}'
        }) 