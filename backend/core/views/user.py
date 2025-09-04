from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.contrib.auth.models import User
from urllib.parse import urlencode
from django.conf import settings
from rest_framework.authtoken.models import Token
from core.serializers import UserRegisterSerializer, UserViewSerializer
from core.services.encryption import verify_verification_token


class UserRegisterView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "User created successfully. Please check your email to verify your account."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = []

    def get(self, request, token):
        frontend_login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"

        try:
            payload, error = verify_verification_token(token)

            if error:
                query_params = urlencode({'error': error})
                return redirect(f"{frontend_login_url}?{query_params}")

            try:
                user = User.objects.get(id=payload['user_id'], email=payload['email'])

                if getattr(user, 'is_active', False):
                    query_params = urlencode({'error': 'This verification link has already been used.'})
                    return redirect(f"{frontend_login_url}?{query_params}")

                user.is_active = True
                user.save()

                token_obj, _ = Token.objects.get_or_create(user=user)

                query_params = urlencode({'token': token_obj.key})
                return redirect(f"{frontend_login_url}?{query_params}")

            except User.DoesNotExist:
                query_params = urlencode({'error': 'User not found.'})
                return redirect(f"{frontend_login_url}?{query_params}")

        except Exception:
            query_params = urlencode({
                'error': 'Invalid or expired verification link. Please try registering again.',
                'isVerified': 'false'
            })
            return redirect(f"{frontend_login_url}?{query_params}")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserViewSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
