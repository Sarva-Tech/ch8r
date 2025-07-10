from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from core.models import ApplicationWidgetToken

class IsAuthenticatedOrWidget(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and request.user.is_authenticated
        ) or (
            hasattr(request, 'application') and request.application is not None
        )


class WidgetTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        print('hello', request.headers.get('Authorization'))
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            widget_token = ApplicationWidgetToken.objects.get(key=token, is_active=True)
            request.application = widget_token.application
            return None, None
        except ApplicationWidgetToken.DoesNotExist:
            raise AuthenticationFailed('Invalid or inactive widget token')
