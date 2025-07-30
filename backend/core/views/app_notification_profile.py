from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Application, AppNotificationProfile
from core.serializers import AppNotificationProfileSerializer


class AppNotificationProfileCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AppNotificationProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        application_id = request.query_params.get("application_id")
        if not application_id:
            return Response(
                {"detail": "application_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        application = get_object_or_404(Application, id=application_id)
        profiles = AppNotificationProfile.objects.filter(application=application)
        serializer = AppNotificationProfileSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
