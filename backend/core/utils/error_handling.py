import logging
import traceback
from typing import Optional, Dict, Any, Callable
from functools import wraps
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)


class GitHubIngestionError(Exception):
    """Custom exception for GitHub ingestion errors"""
    pass


class AIProviderError(Exception):
    """Custom exception for AI provider errors"""
    pass


class ValidationError(Exception):
    """Custom validation error"""
    pass


def handle_service_errors(
    error_class: type = Exception,
    default_message: str = "An error occurred",
    log_level: str = "error"
):
    """
    Decorator for consistent error handling in services
    
    Args:
        error_class: Exception class to raise
        default_message: Default error message
        log_level: Logging level ('error', 'warning', 'info')
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_method = getattr(logger, log_level)
                
                log_method(
                    f"Error in {func.__name__}: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                
                raise error_class(default_message) from e
        
        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    default_value: Any = None,
    error_message: Optional[str] = None
) -> Any:
    """
    Safely execute a function and return default value on error
    
    Args:
        func: Function to execute
        default_value: Value to return on error
        error_message: Optional error message to log
        
    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        if error_message:
            logger.warning(f"{error_message}: {str(e)}")
        else:
            logger.warning(f"Error in {func.__name__}: {str(e)}")
        return default_value


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present in data
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")


def log_api_call(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    response_status: Optional[int] = None,
    error: Optional[str] = None
):
    """
    Log API call details for debugging and monitoring
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        params: Request parameters
        response_status: Response status code
        error: Error message if any
    """
    log_data = {
        'endpoint': endpoint,
        'method': method,
        'params': params or {}
    }
    
    if response_status:
        log_data['status'] = response_status
    
    if error:
        log_data['error'] = error
        logger.error(f"API call failed: {log_data}")
    else:
        logger.info(f"API call: {log_data}")


class ErrorContext:
    """Context manager for error handling and logging"""
    
    def __init__(
        self, 
        operation: str, 
        reraise: bool = True,
        default_return: Any = None
    ):
        self.operation = operation
        self.reraise = reraise
        self.default_return = default_return
    
    def __enter__(self):
        logger.info(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            logger.info(f"Completed operation: {self.operation}")
            return True
        
        logger.error(
            f"Failed operation: {self.operation}\\n"
            f"Error: {exc_val}\\n"
            f"Traceback: {traceback.format_exception(exc_type, exc_val, exc_tb)}"
        )
        
        if self.reraise:
            return False
        
        return True  # Suppress the exception


def format_error_response(
    error: Exception,
    user_friendly_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Format error response for API endpoints
    
    Args:
        error: Exception that occurred
        user_friendly_message: Optional user-friendly message
        
    Returns:
        Formatted error response
    """
    response = {
        'error': user_friendly_message or 'An unexpected error occurred',
        'type': error.__class__.__name__
    }
    
    if logger.isEnabledFor(logging.DEBUG):
        response['details'] = str(error)
        response['traceback'] = traceback.format_exc()
    
    return response
