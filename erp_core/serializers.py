from rest_framework import serializers
from erp_core.models import Customer, User, UserProfile, Department
from inventory.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'modified_at']

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

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description']

class UserProfileSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = ['department', 'department_id', 'phone_number', 'employee_id', 'is_department_head']
        read_only_fields = ['is_department_head']
        extra_kwargs = {
            'phone_number': {'required': False},
            'employee_id': {'required': False}
        }

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password',
                  'role', 'is_active', 'profile', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'role': {'required': False}
        }

    def validate(self, attrs):
        if 'password' in attrs or 'confirm_password' in attrs:
            if attrs.get('password') != attrs.get('confirm_password'):
                raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        validated_data.pop('confirm_password', None)
        
        # Create the user
        user = User.objects.create_user(**validated_data)

        # Create the profile if necessary
        if user.username != 'AnonymousUser':
            # Use the provided employee_id if available; otherwise, use a default
            employee_id = profile_data.pop('employee_id', f'EMP{user.id:04d}')
            UserProfile.objects.create(user=user, employee_id=employee_id, **profile_data)
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        password = validated_data.pop('password', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        
        # Ensure profile exists
        if not hasattr(instance, 'profile'):
            UserProfile.objects.create(user=instance)
        
        # Update profile if data is provided
        if profile_data is not None:
            profile = instance.profile
            for field, value in profile_data.items():
                setattr(profile, field, value)
            profile.save()
        
        return instance