from django.core.cache import cache
from rest_framework.throttling import BaseThrottle
from rest_framework.exceptions import Throttled
import time


class WidgetRateLimiter:
    def __init__(self):
        pass

    @staticmethod
    def get_cache_key(widget_token_key, sender_identifier):
        return f"widget_rate_limit:{widget_token_key}:{sender_identifier}"

    @staticmethod
    def check_rate_limit(widget_token, sender_identifier=None):
        if not sender_identifier:
            sender_identifier = 'anonymous'

        cache_key = WidgetRateLimiter.get_cache_key(widget_token.key, sender_identifier)
        
        current_data = cache.get(cache_key)
        
        if current_data is None:
            cache.set(cache_key, {'count': 1, 'window_start': time.time()}, widget_token.rate_limit_period)
            return True, None
        
        current_time = time.time()
        window_start = current_data['window_start']
        window_elapsed = current_time - window_start
        
        if window_elapsed >= widget_token.rate_limit_period:
            cache.set(cache_key, {'count': 1, 'window_start': current_time}, widget_token.rate_limit_period)
            return True, None
        
        if current_data['count'] >= widget_token.rate_limit_count:
            retry_after = int(widget_token.rate_limit_period - window_elapsed)
            return False, retry_after
        
        current_data['count'] += 1
        cache.set(cache_key, current_data, widget_token.rate_limit_period)
        return True, None


class WidgetRateThrottle(BaseThrottle):
    def __init__(self):
        self.widget_token = None
        self.sender_identifier = None
    
    def get_cache_key(self):
        if not self.widget_token:
            return None
        return f"widget_rate_limit:{self.widget_token.key}:{self.sender_identifier}"
    
    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        
        self.widget_token = getattr(request, 'widget_token', None)
        if not self.widget_token:
            return True
        
        self.sender_identifier = (
            request.data.get('sender_identifier')
            or request.query_params.get('sender_identifier')
            or 'anonymous'
        )
        
        allowed, _ = WidgetRateLimiter.check_rate_limit(self.widget_token, self.sender_identifier)
        return allowed
    
    def wait(self):
        if not self.widget_token:
            return 0
        
        cache_key = self.get_cache_key()
        if not cache_key:
            return 0
        
        current_data = cache.get(cache_key)
        if not current_data:
            return 0
        
        current_time = time.time()
        window_start = current_data['window_start']
        window_elapsed = current_time - window_start
        retry_after = int(self.widget_token.rate_limit_period - window_elapsed)
        return max(0, retry_after)
