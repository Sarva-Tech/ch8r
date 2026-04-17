import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.models import Application, NotificationProfile, AppNotificationProfile, Integration
from core.serializers.configure_app import (
    LoadAppConfigurationSerializer,
    ConfigureAppIntegrationSerializer,
)
from core.tests.factories import UserFactory, ApplicationFactory, NotificationProfileFactory, IntegrationFactory


@pytest.mark.unit
class TestLoadAppConfigurationSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        mock_request = Mock()
        mock_request.user = user

        serializer = LoadAppConfigurationSerializer(application, context={'request': mock_request})
        data = serializer.data

        expected_fields = ['id', 'uuid', 'name', 'llm_models', 'integrations', 'notification_profiles']
        for field in expected_fields:
            assert field in data

    def test_get_notification_profiles_returns_user_profiles(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        profile = NotificationProfileFactory(owner=user)

        mock_request = Mock()
        mock_request.user = user

        serializer = LoadAppConfigurationSerializer(application, context={'request': mock_request})
        profiles = serializer.get_notification_profiles(application)

        assert len(profiles) == 1
        assert profiles[0]['id'] == profile.id

    def test_get_notification_profiles_includes_is_enabled(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        profile = NotificationProfileFactory(owner=user)
        AppNotificationProfile.objects.create(
            application=application,
            notification_profile=profile
        )

        mock_request = Mock()
        mock_request.user = user

        serializer = LoadAppConfigurationSerializer(application, context={'request': mock_request})
        profiles = serializer.get_notification_profiles(application)

        assert profiles[0]['is_enabled'] is True

    def test_get_notification_profiles_is_enabled_false_when_not_configured(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        profile = NotificationProfileFactory(owner=user)

        mock_request = Mock()
        mock_request.user = user

        serializer = LoadAppConfigurationSerializer(application, context={'request': mock_request})
        profiles = serializer.get_notification_profiles(application)

        assert profiles[0]['is_enabled'] is False


@pytest.mark.unit
class TestConfigureAppIntegrationSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        mock_request = Mock()
        mock_request.user = user

        serializer = ConfigureAppIntegrationSerializer(context={'request': mock_request, 'application': application})
        expected_fields = ['integration', 'type', 'branch_name']
        for field in expected_fields:
            assert field in serializer.fields

    def test_init_filters_queryset_for_user(self):
        user = UserFactory()
        user_integration = IntegrationFactory(creator=user)
        other_user = UserFactory()
        other_integration = IntegrationFactory(creator=other_user)

        mock_request = Mock()
        mock_request.user = user

        serializer = ConfigureAppIntegrationSerializer(context={'request': mock_request})
        assert user_integration in serializer.fields['integration'].queryset
        assert other_integration not in serializer.fields['integration'].queryset

    def test_validate_integration_owner_matches_application_owner(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)

        serializer = ConfigureAppIntegrationSerializer(context={'application': application})
        result = serializer.validate_integration(integration)

        assert result == integration

    def test_validate_integration_owner_mismatch(self):
        user_a = UserFactory()
        user_b = UserFactory()
        application = ApplicationFactory(owner=user_a)
        integration = IntegrationFactory(creator=user_b)

        serializer = ConfigureAppIntegrationSerializer(context={'application': application})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_integration(integration)

        assert "owner mismatch" in str(exc_info.value)

    def test_validate_integration_type_matches(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user, provider='github')

        attrs = {
            'integration': integration,
            'type': 'version_control'
        }

        serializer = ConfigureAppIntegrationSerializer(context={'application': application})
        result = serializer.validate(attrs)

        assert result == attrs

    def test_validate_branch_name_required_for_github_pms(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user, provider='github')

        attrs = {
            'integration': integration,
            'type': 'pms',
            'branch_name': ''
        }

        serializer = ConfigureAppIntegrationSerializer(context={'application': application})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate(attrs)

        assert "Branch is required" in str(exc_info.value)

    def test_validate_branch_name_not_required_for_non_pms(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user, provider='github')

        attrs = {
            'integration': integration,
            'type': 'version_control',
            'branch_name': ''
        }

        serializer = ConfigureAppIntegrationSerializer(context={'application': application})
        result = serializer.validate(attrs)

        assert result == attrs

    def test_validate_branch_name_not_required_for_non_github(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user, provider='jira')

        attrs = {
            'integration': integration,
            'type': 'pms',
            'branch_name': ''
        }

        serializer = ConfigureAppIntegrationSerializer(context={'application': application})
        result = serializer.validate(attrs)

        assert result == attrs
