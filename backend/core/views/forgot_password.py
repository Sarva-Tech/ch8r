from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

from core.serializers import ForgotPasswordSerializer
from core.services.encryption import generate_verification_token
from core.tasks.email import send_verification_email_task

class ForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            token = generate_verification_token(user.id, user.email)

            send_verification_email_task.delay(user.id, user.email, user.username, token, purpose="RESET_PASSWORD")

            return Response(
                {"message": "Password reset link sent to your email."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
