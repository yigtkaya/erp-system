# core/middleware.py
from threading import local
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model

User = get_user_model()
_thread_locals = local()


class CurrentUserMiddleware(MiddlewareMixin):
    """
    Middleware to store the current user in thread-local storage
    for use in model save methods
    """
    
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
    
    def process_response(self, request, response):
        if hasattr(_thread_locals, 'user'):
            delattr(_thread_locals, 'user')
        return response


def get_current_user():
    """Get the current user from thread-local storage"""
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    """Set the current user in thread-local storage"""
    _thread_locals.user = user