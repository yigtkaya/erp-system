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

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=True)
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirm_password', 
                 'role', 'is_active', 'profile', 'created_at']
        read_only_fields = ['created_at']

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        validated_data.pop('confirm_password')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'VIEWER'),
            is_active=validated_data.get('is_active', True)
        )
        
        UserProfile.objects.create(
            user=user,
            department_id=profile_data.get('department_id'),
            phone_number=profile_data.get('phone_number', ''),
            employee_id=profile_data['employee_id']
        )
        
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        
        if profile_data and hasattr(instance, 'profile'):
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
            
        return instance