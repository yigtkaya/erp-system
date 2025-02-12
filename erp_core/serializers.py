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
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)

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
        validated_data.pop('confirm_password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        
        if profile_data and hasattr(instance, 'profile'):
            profile = instance.profile
            if 'department_id' in profile_data:
                profile.department_id = profile_data['department_id']
            if 'phone_number' in profile_data:
                profile.phone_number = profile_data['phone_number']
            if 'employee_id' in profile_data:
                profile.employee_id = profile_data['employee_id']
            profile.save()
            
        return instance