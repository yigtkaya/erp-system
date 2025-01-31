from rest_framework.throttling import ScopedRateThrottle

class CustomScopedRateThrottle(ScopedRateThrottle):
    def allow_request(self, request, view):
        if request.user.is_authenticated and request.user.is_superuser:
            return True  # Bypass throttle for admins
        return super().allow_request(request, view) 