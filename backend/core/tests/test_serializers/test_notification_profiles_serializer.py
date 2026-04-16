import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.models import NotificationProfile
from core.serializers.notification_profiles import NotificationProfileSerializer
from core.tests.factories import UserFactory, NotificationProfileFactory


@pytest.mark.unit
class TestNotificationProfileSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        profile = NotificationProfileFactory(owner=user)

        serializer = NotificationProfileSerializer(profile)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'type', 'config', 'created_at', 'name', 'owner']
        for field in expected_fields:
            assert field in data

    def test_read_only_fields(self):
        serializer = NotificationProfileSerializer()
        assert serializer.fields['id'].read_only
        assert serializer.fields['created_at'].read_only
        assert serializer.fields['owner'].read_only

    def test_create_with_config(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        data = {
            'name': 'Test Profile',
            'type': 'email',
            'config': {'email': 'test@example.com'}
        }

        serializer = NotificationProfileSerializer(data=data)
        assert serializer.is_valid()
        profile = serializer.save(owner=user)

        assert profile.name == 'Test Profile'
        assert profile.type == 'email'
        assert profile.config == {'email': 'test@example.com'}

    def test_create_without_config(self):
        user = UserFactory()

        data = {
            'name': 'Test Profile',
            'type': 'email',
            'config': {}
        }

        serializer = NotificationProfileSerializer(data=data)
        assert serializer.is_valid()
        profile = serializer.save(owner=user)

        assert profile.name == 'Test Profile'
        assert profile.type == 'email'

    def test_update_with_config_email(self):
        user = UserFactory()
        profile = NotificationProfileFactory(owner=user, type='email')

        data = {
            'config': {'email': 'new@example.com'}
        }

        serializer = NotificationProfileSerializer(instance=profile, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.config == {'email': 'new@example.com'}

    def test_update_with_config_webhookUrl(self):
        user = UserFactory()
        profile = NotificationProfileFactory(owner=user, type='slack')

        data = {
            'config': {'webhookUrl': 'https://hooks.slack.com/test'}
        }

        serializer = NotificationProfileSerializer(instance=profile, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.config == {'webhookUrl': 'https://hooks.slack.com/test'}

    def test_update_with_config_webhook_url(self):
        user = UserFactory()
        profile = NotificationProfileFactory(owner=user, type='slack')

        data = {
            'config': {'webhook_url': 'https://hooks.slack.com/test'}
        }

        serializer = NotificationProfileSerializer(instance=profile, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.config == {'webhookUrl': 'https://hooks.slack.com/test'}

    def test_update_without_config(self):
        user = UserFactory()
        profile = NotificationProfileFactory(owner=user, name='Old Name')

        data = {
            'name': 'New Name'
        }

        serializer = NotificationProfileSerializer(instance=profile, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.name == 'New Name'

    def test_to_representation_returns_safe_config_email(self):
        user = UserFactory()
        profile = NotificationProfileFactory(owner=user, type='email')

        serializer = NotificationProfileSerializer(profile)
        data = serializer.data

        assert 'config' in data
        assert data['config'] == {'email': profile.config.get('email')}

    def test_to_representation_returns_safe_config_webhook(self):
        user = UserFactory()
        profile = NotificationProfileFactory(owner=user, type='slack')

        serializer = NotificationProfileSerializer(profile)
        data = serializer.data

        assert 'config' in data
        assert 'webhookUrl' in data['config']

    def test_to_representation_handles_empty_config(self):
        user = UserFactory()
        profile = NotificationProfileFactory(owner=user, type='email')

        serializer = NotificationProfileSerializer(profile)
        data = serializer.data

        assert 'config' in data
        assert data['config'] == {'email': profile.config.get('email')}
