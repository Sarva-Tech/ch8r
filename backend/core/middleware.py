from django.utils.deprecation import MiddlewareMixin
from core.models import AccountStatus
from rest_framework.authtoken.models import Token
from django.http import JsonResponse


class AccountStatusMiddleware(MiddlewareMixin):
    EXCLUDED_PATHS = [
        '/api/register/',
        '/api/login/',
        '/api/verify-email/',
    ]

    def process_request(self, request):
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return None

        if request.method != 'OPTIONS' and request.path.startswith('/api/'):
            auth_header = request.headers.get('Authorization')

            if not auth_header or (not auth_header.startswith('Bearer ') and not auth_header.startswith('Token ')):
                return JsonResponse(
                    {"error": "Authorization header missing or invalid"},
                    status=401,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization"
                    }
                )

            try:
                token_key = auth_header.split(' ')[1]
                if token_key.startswith('widget_'):
                    return None

                token = Token.objects.get(key=token_key)
                account_status = AccountStatus.objects.filter(account=token.user).first()

                if not account_status or account_status.status != 'ACTIVE':
                    return JsonResponse(
                        {"error": "Your account approval is pending. We will get back to you as soon as the verification is complete. Thank you for your patience. Please contact our support team for any queries.",
                         "account_status": account_status.status if account_status else "NONE"},
                        status=403,
                        headers={
                            "Access-Control-Allow-Origin": "*",
                            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
                            "Access-Control-Allow-Headers": "Content-Type, Authorization"
                        }
                    )

            except IndexError:
                return JsonResponse(
                    {"error": "Malformed Authorization header"},
                    status=401,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization"
                    }
                )
            except Token.DoesNotExist:
                return JsonResponse(
                    {"error": "Invalid token"},
                    status=401,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization"
                    }
                )
            except Exception as e:
                return JsonResponse(
                    {"error": "Internal server error"},
                    status=500,
                    headers={
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization"
                    }
                )

        return None
