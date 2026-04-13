from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if isinstance(exc, Throttled) and response is not None:
        request = context.get('request')
        
        widget_token = getattr(request, 'widget_token', None)
        if widget_token:
            response.headers['X-RateLimit-Limit'] = str(widget_token.rate_limit_count)
            response.headers['X-RateLimit-Period'] = str(widget_token.rate_limit_period)
            
            if isinstance(response.data, dict):
                response.data['rate_limit_count'] = widget_token.rate_limit_count
                response.data['rate_limit_period'] = widget_token.rate_limit_period
                response.data['retry_after'] = getattr(exc, 'wait', None)
    
    return response
