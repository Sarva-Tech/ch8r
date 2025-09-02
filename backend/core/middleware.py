from django.utils.deprecation import MiddlewareMixin
from core.models import AccountStatus
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import PermissionDenied
from django.http import JsonResponse

class AccountStatusMiddleware(MiddlewareMixin):
    EXCLUDED_PATHS = [
        '/api/register/',
        '/api/login/'
    ]

    def process_request(self, request):
        if request.method != 'OPTIONS' and request.path.startswith('/api/') and request.path not in self.EXCLUDED_PATHS:
            auth_header = request.headers.get('Authorization')
            token_key = auth_header.split(' ')[1]

            if token_key.startswith('widget_'):
                return None

            token = Token.objects.get(key=token_key)
            account_status = AccountStatus.objects.filter(account__email=token.user).first()

            if not account_status or account_status.status != 'ACTIVE':
                return JsonResponse(
                        {"account_status": account_status.status},
                        status=403,
                        headers={
                                "Access-Control-Allow-Origin": "*",
                                "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
                                "Access-Control-Allow-Headers": "Content-Type, Authorization"
                            }
                    )

            return None
