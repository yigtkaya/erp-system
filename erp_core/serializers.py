from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['departments'] = list(user.departments.values_list('name', flat=True))
        token['permissions'] = list(user.get_all_permissions())

        return token 