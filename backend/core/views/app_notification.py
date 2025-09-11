from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView

from core.models import Application, NotificationProfile, AppNotificationProfile
from core.serializers import LoadAppConfigurationSerializer


class AppNotificationUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, app_uuid):
        application = get_object_or_404(Application, uuid=app_uuid, owner=request.user)

        profile_uuids = request.data.get("profile_uuids", [])
        if not isinstance(profile_uuids, list):
            return Response(
                {"detail": "profile_uuids must be a list of UUIDs"},
                status=status.HTTP_400_BAD_REQUEST
            )

        AppNotificationProfile.objects.filter(application=application).delete()

        profiles = NotificationProfile.objects.filter(
            uuid__in=profile_uuids, owner=request.user
        )
        app_profiles = [
            AppNotificationProfile(application=application, notification_profile=p)
            for p in profiles
        ]
        AppNotificationProfile.objects.bulk_create(app_profiles)

        serializer = LoadAppConfigurationSerializer(application, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
