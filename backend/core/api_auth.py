from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import APIToken

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Token "):
            return None

        token_key = auth_header.split(" ")[1]
        try:
            token = APIToken.objects.get(key=token_key, is_active=True)
            return token.user, token
        except APIToken.DoesNotExist:
            raise AuthenticationFailed("Invalid or inactive API token")
