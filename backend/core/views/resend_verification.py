from django.contrib.auth.models import User
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from core.services.encryption import generate_verification_token
from core.tasks.email import send_verification_email_task
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response(
                    {'message': 'This email is already verified. You can log in.'},
                    status=status.HTTP_200_OK
                )

            verification_token = generate_verification_token(user.id, user.email)

            send_verification_email_task.delay(
                user.id,
                user.email,
                user.username,
                verification_token,
                purpose="VERIFY_EMAIL"
            )

            logger.info(f"Verification email resent to: {email}")

            return Response(
                {'message': 'Verification email has been sent. Please check your inbox.'},
                status=status.HTTP_200_OK
            )

        except ObjectDoesNotExist:
            return Response(
                {'message': 'If this email exists, a verification email has been sent.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error resending verification email to {email}: {str(e)}")
            return Response(
                {'error': 'Failed to send verification email. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
