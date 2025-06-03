"""
Manufacturing module custom exceptions and standardized error messages
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

# Configure logger
logger = logging.getLogger('manufacturing.exceptions')


class ManufacturingException(Exception):
    """Base exception for manufacturing operations"""
    default_message = "An error occurred in manufacturing operations"
    default_code = "MANUFACTURING_ERROR"
    
    def __init__(self, message=None, code=None, details=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)


class WorkOrderException(ManufacturingException):
    """Exceptions related to work order operations"""
    default_message = "Work order operation failed"
    default_code = "WORK_ORDER_ERROR"


class MachineException(ManufacturingException):
    """Exceptions related to machine operations"""
    default_message = "Machine operation failed"
    default_code = "MACHINE_ERROR"


class MaterialAllocationException(ManufacturingException):
    """Exceptions related to material allocation"""
    default_message = "Material allocation failed"
    default_code = "MATERIAL_ALLOCATION_ERROR"


class ProductionException(ManufacturingException):
    """Exceptions related to production operations"""
    default_message = "Production operation failed"
    default_code = "PRODUCTION_ERROR"


class BusinessRuleViolationException(ManufacturingException):
    """Exceptions for business rule violations"""
    default_message = "Business rule violation detected"
    default_code = "BUSINESS_RULE_VIOLATION"


# Standardized error messages
class ErrorMessages:
    """Centralized error messages for manufacturing operations"""
    
    # Work Order Errors
    WORK_ORDER_NOT_FOUND = "Work order not found"
    WORK_ORDER_INVALID_STATUS = "Invalid work order status for this operation"
    WORK_ORDER_ALREADY_STARTED = "Work order has already been started"
    WORK_ORDER_ALREADY_COMPLETED = "Work order is already completed"
    WORK_ORDER_CANNOT_START = "Work order cannot be started in current status"
    WORK_ORDER_NO_MATERIALS = "Cannot start work order without allocated materials"
    WORK_ORDER_NO_MACHINE = "Work order must have a machine assigned"
    WORK_ORDER_INVALID_DATES = "Planned end date must be after planned start date"
    WORK_ORDER_QUANTITY_INVALID = "Completed quantity cannot exceed ordered quantity"
    WORK_ORDER_OPERATION_SEQUENCE_INVALID = "Operation sequence must be unique within work order"
    
    # Machine Errors
    MACHINE_NOT_FOUND = "Machine not found"
    MACHINE_NOT_AVAILABLE = "Machine is not available for production"
    MACHINE_UNDER_MAINTENANCE = "Machine is currently under maintenance"
    MACHINE_BROKEN = "Machine is marked as broken and cannot be used"
    MACHINE_ALREADY_IN_USE = "Machine is already assigned to another work order"
    MACHINE_MAINTENANCE_OVERDUE = "Machine maintenance is overdue"
    MACHINE_INVALID_STATUS = "Invalid machine status transition"
    
    # Material Allocation Errors
    MATERIAL_NOT_FOUND = "Material not found"
    MATERIAL_INSUFFICIENT_STOCK = "Insufficient stock for material allocation"
    MATERIAL_ALREADY_ALLOCATED = "Materials are already allocated for this work order"
    MATERIAL_ALLOCATION_EXCEEDED = "Allocated quantity cannot exceed required quantity"
    MATERIAL_NOT_ALLOCATED = "Materials must be allocated before issuing"
    MATERIAL_BOM_NOT_FOUND = "No BOM found for this product"
    MATERIAL_INVALID_QUANTITY = "Invalid material quantity specified"
    
    # Production Errors
    PRODUCTION_OUTPUT_INVALID = "Invalid production output data"
    PRODUCTION_QUANTITY_NEGATIVE = "Production quantities cannot be negative"
    PRODUCTION_NO_OPERATOR = "Production output requires an operator"
    PRODUCTION_OPERATION_NOT_STARTED = "Operation must be started before recording output"
    PRODUCTION_ALREADY_COMPLETED = "Production for this operation is already completed"
    
    # Operation Errors
    OPERATION_NOT_FOUND = "Operation not found"
    OPERATION_INVALID_SEQUENCE = "Invalid operation sequence"
    OPERATION_ALREADY_STARTED = "Operation has already been started"
    OPERATION_ALREADY_COMPLETED = "Operation is already completed"
    OPERATION_CANNOT_START = "Operation cannot be started in current status"
    OPERATION_MACHINE_CONFLICT = "Machine is not available for this operation"
    
    # General Validation Errors
    VALIDATION_REQUIRED_FIELD = "This field is required"
    VALIDATION_INVALID_FORMAT = "Invalid format provided"
    VALIDATION_INVALID_CHOICE = "Invalid choice selected"
    VALIDATION_DUPLICATE_VALUE = "This value already exists"
    VALIDATION_INSUFFICIENT_PERMISSIONS = "Insufficient permissions for this operation"
    
    # System Errors
    SYSTEM_ERROR = "A system error occurred. Please try again later"
    SYSTEM_DATABASE_ERROR = "Database operation failed"
    SYSTEM_INTEGRATION_ERROR = "Integration with external system failed"


def get_standardized_error_response(error_code, message=None, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Generate standardized error response format
    """
    return {
        'success': False,
        'error': {
            'code': error_code,
            'message': message or ErrorMessages.SYSTEM_ERROR,
            'details': details or {}
        }
    }


def manufacturing_exception_handler(exc, context):
    """
    Custom exception handler for manufacturing module
    """
    # Get the standard DRF response
    response = exception_handler(exc, context)
    
    # Handle custom manufacturing exceptions
    if isinstance(exc, ManufacturingException):
        custom_response_data = get_standardized_error_response(
            error_code=exc.code,
            message=exc.message,
            details=exc.details
        )
        
        # Log the error
        logger.error(f"Manufacturing Exception: {exc.code} - {exc.message}", 
                    extra={'details': exc.details, 'context': context})
        
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle Django validation errors
    elif isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message_dict'):
            # Field validation errors
            details = exc.message_dict
        elif hasattr(exc, 'messages'):
            # Non-field validation errors
            details = {'non_field_errors': exc.messages}
        else:
            details = {'error': str(exc)}
        
        custom_response_data = get_standardized_error_response(
            error_code='VALIDATION_ERROR',
            message='Validation failed',
            details=details
        )
        
        logger.warning(f"Validation Error: {str(exc)}", extra={'details': details})
        
        return Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # If it's a standard DRF response, enhance it with our format
    if response is not None:
        # Check if it's already in our format
        if 'success' not in response.data:
            custom_response_data = get_standardized_error_response(
                error_code='API_ERROR',
                message=response.data.get('detail', 'An error occurred'),
                details=response.data,
                status_code=response.status_code
            )
            response.data = custom_response_data
    
    return response


# Helper functions for common validations
class ValidationHelpers:
    """Helper functions for common manufacturing validations"""
    
    @staticmethod
    def validate_work_order_status_transition(from_status, to_status):
        """Validate work order status transitions"""
        valid_transitions = {
            'DRAFT': ['PLANNED', 'CANCELLED'],
            'PLANNED': ['RELEASED', 'CANCELLED', 'ON_HOLD'],
            'RELEASED': ['IN_PROGRESS', 'ON_HOLD', 'CANCELLED'],
            'IN_PROGRESS': ['COMPLETED', 'ON_HOLD', 'CANCELLED'],
            'ON_HOLD': ['RELEASED', 'CANCELLED'],
            'COMPLETED': [],  # Terminal state
            'CANCELLED': []   # Terminal state
        }
        
        if to_status not in valid_transitions.get(from_status, []):
            raise WorkOrderException(
                message=f"Cannot transition from {from_status} to {to_status}",
                code="INVALID_STATUS_TRANSITION",
                details={'from_status': from_status, 'to_status': to_status}
            )
    
    @staticmethod
    def validate_machine_availability(machine, exclude_work_order=None):
        """Validate machine availability for work order assignment"""
        if not machine.is_active:
            raise MachineException(
                message=ErrorMessages.MACHINE_NOT_AVAILABLE,
                code="MACHINE_INACTIVE",
                details={'machine_code': machine.machine_code}
            )
        
        if machine.status == 'MAINTENANCE':
            raise MachineException(
                message=ErrorMessages.MACHINE_UNDER_MAINTENANCE,
                code="MACHINE_MAINTENANCE",
                details={'machine_code': machine.machine_code}
            )
        
        if machine.status == 'BROKEN':
            raise MachineException(
                message=ErrorMessages.MACHINE_BROKEN,
                code="MACHINE_BROKEN",
                details={'machine_code': machine.machine_code}
            )
        
        if machine.is_maintenance_overdue:
            raise MachineException(
                message=ErrorMessages.MACHINE_MAINTENANCE_OVERDUE,
                code="MACHINE_MAINTENANCE_OVERDUE",
                details={'machine_code': machine.machine_code}
            )
    
    @staticmethod
    def validate_material_allocation_quantity(required_quantity, allocated_quantity):
        """Validate material allocation quantities"""
        if allocated_quantity < 0:
            raise MaterialAllocationException(
                message="Allocated quantity cannot be negative",
                code="NEGATIVE_QUANTITY"
            )
        
        if allocated_quantity > required_quantity:
            raise MaterialAllocationException(
                message=ErrorMessages.MATERIAL_ALLOCATION_EXCEEDED,
                code="ALLOCATION_EXCEEDED",
                details={
                    'required_quantity': str(required_quantity),
                    'allocated_quantity': str(allocated_quantity)
                }
            )
    
    @staticmethod
    def validate_production_quantities(quantity_good, quantity_scrapped, max_quantity=None):
        """Validate production output quantities"""
        if quantity_good < 0:
            raise ProductionException(
                message="Good quantity cannot be negative",
                code="NEGATIVE_GOOD_QUANTITY"
            )
        
        if quantity_scrapped < 0:
            raise ProductionException(
                message="Scrapped quantity cannot be negative",
                code="NEGATIVE_SCRAPPED_QUANTITY"
            )
        
        if max_quantity and (quantity_good + quantity_scrapped) > max_quantity:
            raise ProductionException(
                message="Total output cannot exceed ordered quantity",
                code="OUTPUT_EXCEEDS_ORDER",
                details={
                    'quantity_good': quantity_good,
                    'quantity_scrapped': quantity_scrapped,
                    'total_output': quantity_good + quantity_scrapped,
                    'max_quantity': max_quantity
                }
            ) 