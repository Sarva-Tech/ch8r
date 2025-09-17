from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import redirect
from urllib.parse import urlencode
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from core.serializers import ResetPasswordSerializer
from core.services.encryption import verify_verification_token


class ResetPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        payload, error = verify_verification_token(token)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(id=payload['user_id'], email=payload['email'])
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordVerifyView(APIView):
    permission_classes = []

    def get(self, request, token):

        frontend_reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password"

        try:
            payload, error = verify_verification_token(token)

            if error:
                query_params = urlencode({'error': error, 'isVerified': 'false'})
                return redirect(f"{frontend_reset_url}?{query_params}")

            try:
                user = User.objects.get(id=payload['user_id'], email=payload['email'])
                query_params = urlencode({'token': token})
                return redirect(f"{frontend_reset_url}?{query_params}")

            except User.DoesNotExist:
                query_params = urlencode({'error': 'User not found', 'isVerified': 'false'})
                return redirect(f"{frontend_reset_url}?{query_params}")

        except Exception:
            query_params = urlencode({
                'error': 'Invalid or expired link. Please request a new password reset.',
                'isVerified': 'false'
            })
            return redirect(f"{frontend_reset_url}?{query_params}")
