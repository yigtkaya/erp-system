from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from erp_core.models import Customer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['departments'] = list(user.departments.values_list('name', flat=True))
        token['permissions'] = list(user.get_all_permissions())

        return token 

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            'id', 'code', 'name', 
            'created_at', 'modified_at',
            'created_by', 'modified_by'
        ]
        read_only_fields = [
            'created_at', 'modified_at',
            'created_by', 'modified_by'
        ]
    
    def validate_code(self, value):
        if not value.isalnum():
            raise serializers.ValidationError("Customer code must be alphanumeric")
        return value