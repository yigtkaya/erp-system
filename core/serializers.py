# core/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import (
    User, Department, Customer, UserProfile, 
    DepartmentMembership, AuditLog, Permission, 
    RolePermission, PrivateDocument
)

User = get_user_model()


class DepartmentSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'created_at', 'member_count']
        read_only_fields = ['created_at']
    
    def get_member_count(self, obj):
        return obj.members.count()


class UserProfileSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'phone_number', 'employee_id', 'is_department_head',
            'department', 'department_id'
        ]
        read_only_fields = ['employee_id']


class DepartmentMembershipSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    
    class Meta:
        model = DepartmentMembership
        fields = ['department', 'joined_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    departments = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'is_active', 'created_at', 'last_login',
            'profile', 'departments'
        ]
        read_only_fields = ['id', 'created_at', 'last_login']
    
    def get_departments(self, obj):
        memberships = DepartmentMembership.objects.filter(user=obj)
        return DepartmentMembershipSerializer(memberships, many=True).data
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for user lists"""
    department = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'role',
            'is_active', 'department'
        ]
    
    def get_department(self, obj):
        if hasattr(obj, 'profile') and obj.profile.department:
            return obj.profile.department.name
        return None
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    profile = UserProfileSerializer(required=False)
    department_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'profile',
            'department_ids'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({
                'password': 'Password fields didn\'t match.'
            })
        return attrs
    
    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        department_ids = validated_data.pop('department_ids', [])
        
        with transaction.atomic():
            # Create user
            user = User.objects.create_user(**validated_data)
            
            # Create profile
            profile_data['user'] = user
            UserProfile.objects.create(**profile_data)
            
            # Create department memberships
            for dept_id in department_ids:
                try:
                    department = Department.objects.get(id=dept_id)
                    DepartmentMembership.objects.create(
                        user=user,
                        department=department
                    )
                except Department.DoesNotExist:
                    continue
            
            return user


class UserUpdateSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'is_active', 'profile'
        ]
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or create profile
        if profile_data is not None:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=False, style={'input_type': 'password'})
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                'password': 'Password fields didn\'t match.'
            })
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})


class CustomerSerializer(serializers.ModelSerializer):
    created_by = UserListSerializer(read_only=True)
    modified_by = UserListSerializer(read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'code', 'name', 'email', 'phone', 'address',
            'created_at', 'updated_at', 'created_by', 'modified_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'modified_by']
    
    def validate_code(self, value):
        import re
        if not re.match(r'^[A-Za-z0-9\.]+$', value):
            raise serializers.ValidationError(
                "Customer code must contain only letters, numbers, and periods"
            )
        if len(value) < 4:
            raise serializers.ValidationError(
                "Customer code must be at least 4 characters"
            )
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    changed_by = UserListSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'table_name', 'record_id', 'action',
            'changed_data', 'changed_by', 'changed_at'
        ]
        read_only_fields = ['__all__']


class PrivateDocumentSerializer(serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PrivateDocument
        fields = ['id', 'title', 'description', 'document', 'document_url', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_document_url(self, obj):
        """
        Generate a temporary URL for the document
        with a 5-minute expiration by default
        """
        # Default to 5 minute expiration
        expire_seconds = self.context.get('expire_seconds', 300)
        return obj.get_document_url(expire_seconds=expire_seconds)