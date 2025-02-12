from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from rest_framework import serializers

from erp_core.models import User, UserProfile
from erp_core.serializers import UserSerializer
from erp_core.permissions import IsAdminUser
from erp_core.helpers.email_utils import send_password_creation_email

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users in the system.
    Only administrators can access these endpoints.
    """
    queryset = User.objects.all().select_related('profile')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    search_fields = ['username', 'email', 'profile__employee_id']
    ordering_fields = ['created_at', 'username', 'email']
    ordering = ['-created_at']

    def get_queryset(self):
        # Optionally, further customize the queryset as needed.
        return self.queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

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
        responses={
            201: UserSerializer(),
            400: "Bad Request",
        },
        tags=['User Management']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the user with an unusable password
        user = serializer.save()
        user.set_unusable_password()
        user.save()
        
        # Send password creation email
        email_sent = send_password_creation_email(user, request)
        
        headers = self.get_success_headers(serializer.data)
        response_data = serializer.data
        response_data['password_email_sent'] = email_sent
        
        return Response(
            response_data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

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
        responses={
            200: UserSerializer(),
            400: "Bad Request with error details"
        },
        tags=['User Management']
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except serializers.ValidationError as e:
            return Response(
                {'detail': e.detail},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Partially update user details",
        request_body=UserSerializer,
        responses={
            200: UserSerializer(),
            400: "Bad Request with error details"
        },
        tags=['User Management']
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

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

@swagger_auto_schema(
    method='post',
    operation_description="Set password using token from email",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['password'],
        properties={
            'password': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={
        200: openapi.Response(
            description="Password set successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                }
            )
        ),
        400: "Invalid token or password",
    },
    tags=['User Management']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def set_password(request, uidb64, token):
    try:
        # Decode the user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Verify the token
        if not default_token_generator.check_token(user, token):
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set the new password
        password = request.data.get('password')
        if not password:
            return Response(
                {'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(password)
        user.save()
        
        return Response({
            'status': 'success',
            'message': 'Password set successfully'
        })
        
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid user ID'},
            status=status.HTTP_400_BAD_REQUEST
        ) 