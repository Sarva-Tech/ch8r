import pytest
from rest_framework import serializers

from core.models import AppNotificationProfile, NotificationProfile
from core.serializers.app_notification_profile import AppNotificationProfileSerializer
from core.tests.factories import UserFactory, ApplicationFactory, NotificationProfileFactory


@pytest.mark.unit
class TestAppNotificationProfileSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        notification_profile = NotificationProfileFactory(owner=user)
        app_notification_profile = AppNotificationProfile(
            application=application,
            notification_profile=notification_profile
        )

        serializer = AppNotificationProfileSerializer(app_notification_profile)
        data = serializer.data

        expected_fields = ['id', 'application', 'notification_profile', 'created_at']
        for field in expected_fields:
            assert field in data

    def test_serialization_includes_nested_notification_profile(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        notification_profile = NotificationProfileFactory(owner=user, type='email')
        app_notification_profile = AppNotificationProfile(
            application=application,
            notification_profile=notification_profile
        )

        serializer = AppNotificationProfileSerializer(app_notification_profile)
        data = serializer.data

        assert 'notification_profile' in data
        assert data['notification_profile']['type'] == 'email'

    def test_serialization_notification_profile_id_is_write_only(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        notification_profile = NotificationProfileFactory(owner=user)
        app_notification_profile = AppNotificationProfile(
            application=application,
            notification_profile=notification_profile
        )

        serializer = AppNotificationProfileSerializer(app_notification_profile)
        data = serializer.data

        assert 'notification_profile_id' not in data

    def test_create_with_notification_profile_id(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        notification_profile = NotificationProfileFactory(owner=user)

        data = {
            'application': application.id,
            'notification_profile_id': notification_profile.id
        }

        serializer = AppNotificationProfileSerializer(data=data)
        assert serializer.is_valid()
        app_notification_profile = serializer.save()

        assert app_notification_profile.application == application
        assert app_notification_profile.notification_profile == notification_profile

    def test_create_without_notification_profile_id(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        data = {
            'application': application.id
        }

        serializer = AppNotificationProfileSerializer(data=data)
        assert not serializer.is_valid()
        assert 'notification_profile_id' in serializer.errors

    def test_update_with_notification_profile_id(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        notification_profile_old = NotificationProfileFactory(owner=user)
        notification_profile_new = NotificationProfileFactory(owner=user)
        app_notification_profile = AppNotificationProfile.objects.create(
            application=application,
            notification_profile=notification_profile_old
        )

        data = {
            'notification_profile_id': notification_profile_new.id
        }

        serializer = AppNotificationProfileSerializer(
            instance=app_notification_profile,
            data=data,
            partial=True
        )
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.notification_profile == notification_profile_new

    def test_unique_together_constraint(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        notification_profile = NotificationProfileFactory(owner=user)

        AppNotificationProfile.objects.create(
            application=application,
            notification_profile=notification_profile
        )

        data = {
            'application': application.id,
            'notification_profile_id': notification_profile.id
        }

        serializer = AppNotificationProfileSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
