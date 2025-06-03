import logging
import json
import functools
from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from core.models import BaseModel

# Configure manufacturing logger
manufacturing_logger = logging.getLogger('manufacturing')

# Create a structured logger for manufacturing operations
class ManufacturingOperationLogger:
    """
    Centralized logging for manufacturing operations
    """
    
    @staticmethod
    def log_work_order_action(user, work_order, action, details=None, success=True):
        """Log work order related actions"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'user_username': user.username if user else 'anonymous',
            'work_order_id': work_order.id if work_order else None,
            'work_order_number': work_order.work_order_number if work_order else None,
            'action': action,
            'success': success,
            'details': details or {}
        }
        
        if success:
            manufacturing_logger.info(f"Work Order Action: {action}", extra=log_data)
        else:
            manufacturing_logger.error(f"Work Order Action Failed: {action}", extra=log_data)
    
    @staticmethod
    def log_machine_action(user, machine, action, details=None, success=True):
        """Log machine related actions"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'user_username': user.username if user else 'anonymous',
            'machine_id': machine.id if machine else None,
            'machine_code': machine.machine_code if machine else None,
            'action': action,
            'success': success,
            'details': details or {}
        }
        
        if success:
            manufacturing_logger.info(f"Machine Action: {action}", extra=log_data)
        else:
            manufacturing_logger.error(f"Machine Action Failed: {action}", extra=log_data)
    
    @staticmethod
    def log_material_allocation(user, work_order, materials_count, action, success=True, details=None):
        """Log material allocation actions"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'user_username': user.username if user else 'anonymous',
            'work_order_id': work_order.id if work_order else None,
            'work_order_number': work_order.work_order_number if work_order else None,
            'materials_count': materials_count,
            'action': action,
            'success': success,
            'details': details or {}
        }
        
        if success:
            manufacturing_logger.info(f"Material Allocation: {action}", extra=log_data)
        else:
            manufacturing_logger.error(f"Material Allocation Failed: {action}", extra=log_data)
    
    @staticmethod
    def log_production_output(user, work_order, quantity_good, quantity_scrapped, success=True, details=None):
        """Log production output recording"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'user_username': user.username if user else 'anonymous',
            'work_order_id': work_order.id if work_order else None,
            'work_order_number': work_order.work_order_number if work_order else None,
            'quantity_good': quantity_good,
            'quantity_scrapped': quantity_scrapped,
            'success': success,
            'details': details or {}
        }
        
        if success:
            manufacturing_logger.info("Production Output Recorded", extra=log_data)
        else:
            manufacturing_logger.error("Production Output Recording Failed", extra=log_data)
    
    @staticmethod
    def log_api_request(user, endpoint, method, request_data=None, response_status=None, execution_time=None):
        """Log API requests"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user and hasattr(user, 'id') else None,
            'user_username': user.username if user and hasattr(user, 'username') else 'anonymous',
            'endpoint': endpoint,
            'method': method,
            'request_data': request_data,
            'response_status': response_status,
            'execution_time_ms': execution_time
        }
        
        manufacturing_logger.info(f"API Request: {method} {endpoint}", extra=log_data)
    
    @staticmethod
    def log_business_rule_violation(user, entity_type, entity_id, rule_name, violation_details):
        """Log business rule violations"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'user_id': user.id if user else None,
            'user_username': user.username if user else 'anonymous',
            'entity_type': entity_type,
            'entity_id': entity_id,
            'rule_name': rule_name,
            'violation_details': violation_details
        }
        
        manufacturing_logger.warning(f"Business Rule Violation: {rule_name}", extra=log_data)
    
    @staticmethod
    def log_system_error(error_type, error_message, context=None):
        """Log system errors"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error_message),
            'context': context or {}
        }
        
        manufacturing_logger.error(f"System Error: {error_type}", extra=log_data)


# Middleware for API request logging
class ManufacturingAPILoggingMiddleware:
    """
    Middleware to log all API requests to manufacturing endpoints
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only log manufacturing API requests
        if request.path.startswith('/api/manufacturing/'):
            start_time = timezone.now()
            
            # Log request
            request_data = None
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    if hasattr(request, 'data'):
                        request_data = dict(request.data)
                    elif request.content_type == 'application/json':
                        request_data = json.loads(request.body.decode('utf-8'))
                except (ValueError, UnicodeDecodeError):
                    request_data = {'error': 'Could not parse request body'}
            
            # Process request
            response = self.get_response(request)
            
            # Calculate execution time
            end_time = timezone.now()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            # Log the request
            ManufacturingOperationLogger.log_api_request(
                user=getattr(request, 'user', None),
                endpoint=request.path,
                method=request.method,
                request_data=request_data,
                response_status=response.status_code,
                execution_time=execution_time
            )
            
            # Also create audit log entry for important operations
            if request.method in ['POST', 'PUT', 'DELETE'] and response.status_code < 400:
                # Import here to avoid circular imports
                from .models import ManufacturingAuditLog
                
                ManufacturingAuditLog.log_action(
                    user=getattr(request, 'user', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                    action_type='API_REQUEST',
                    message=f"{request.method} {request.path}",
                    details={
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code,
                        'execution_time_ms': execution_time
                    },
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
        else:
            response = self.get_response(request)
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Decorator for logging business operations
def log_manufacturing_operation(operation_type, entity_type=None):
    """
    Decorator to automatically log manufacturing business operations
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request/user info
            request = None
            user = None
            
            # Try to find request object in args
            for arg in args:
                if hasattr(arg, 'request'):
                    request = arg.request
                    user = getattr(request, 'user', None)
                    break
                elif hasattr(arg, 'user'):
                    user = arg.user
                    break
            
            start_time = timezone.now()
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                # Log the operation
                execution_time = (timezone.now() - start_time).total_seconds() * 1000
                
                log_details = {
                    'function_name': func.__name__,
                    'execution_time_ms': execution_time,
                    'success': success
                }
                
                if error_message:
                    log_details['error_message'] = error_message
                
                # Import here to avoid circular imports
                from .models import ManufacturingAuditLog
                
                # Create audit log
                ManufacturingAuditLog.log_action(
                    user=user,
                    action_type=operation_type,
                    message=f"{operation_type}: {func.__name__}",
                    log_level='ERROR' if not success else 'INFO',
                    entity_type=entity_type,
                    details=log_details
                )
        
        return wrapper
    return decorator 