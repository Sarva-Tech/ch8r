import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.models import AppIntegration, Integration
from core.serializers.app_integration import (
    AppIntegrationSerializer,
    AppIntegrationCreateSerializer,
    AppIntegrationViewSerializer,
)
from core.tests.factories import UserFactory, IntegrationFactory, ApplicationFactory


@pytest.mark.unit
class TestAppIntegrationSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegration(
            application=application,
            integration=integration,
            integration_type='version_control',
            metadata={'key': 'value'},
            is_active=True
        )

        serializer = AppIntegrationSerializer(app_integration)
        data = serializer.data

        expected_fields = ['uuid', 'integration', 'integration_type', 'metadata', 'is_active', 'created_at', 'updated_at']
        for field in expected_fields:
            assert field in data

    def test_serialization_includes_nested_integration(self):
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user, provider='github')
        app_integration = AppIntegration(
            application=application,
            integration=integration,
            integration_type='version_control'
        )

        serializer = AppIntegrationSerializer(app_integration)
        data = serializer.data

        assert 'integration' in data
        assert data['integration']['provider'] == 'github'

    def test_app_integration_view_serializer_is_alias(self):
        assert AppIntegrationViewSerializer == AppIntegrationSerializer


@pytest.mark.unit
class TestAppIntegrationCreateSerializer:
    def test_validate_integration_uuid_valid_owned(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user)

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(context={'request': mock_request})
        result = serializer.validate_integration_uuid(integration.uuid)

        assert result == integration.uuid
        assert serializer._integration == integration

    def test_validate_integration_uuid_not_found(self):
        user = UserFactory()

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_integration_uuid('00000000-0000-0000-0000-000000000000')

        assert "not found" in str(exc_info.value)

    def test_validate_integration_uuid_unowned(self):
        user_a = UserFactory()
        user_b = UserFactory()
        integration = IntegrationFactory(creator=user_a)

        mock_request = Mock()
        mock_request.user = user_b

        serializer = AppIntegrationCreateSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_integration_uuid(integration.uuid)

        assert "don't own this integration" in str(exc_info.value)

    def test_validate_integration_type_supported(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(context={'request': mock_request})
        serializer._integration = integration

        data = {'integration_type': 'version_control'}
        result = serializer.validate(data)

        assert result == data

    def test_validate_integration_type_unsupported(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(context={'request': mock_request})
        serializer._integration = integration

        data = {'integration_type': 'unsupported_type'}
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate(data)

        assert "not supported" in str(exc_info.value)

    def test_create_new_integration(self):
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        data = {
            'integration_uuid': integration.uuid,
            'integration_type': 'version_control',
            'metadata': {'key': 'value'}
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_integration = serializer.save()

        assert app_integration.application == application
        assert app_integration.integration == integration
        assert app_integration.integration_type == 'version_control'
        assert app_integration.metadata == {'key': 'value'}
        assert app_integration.is_active is True

    def test_create_updates_existing_integration(self):
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        existing = AppIntegration.objects.create(
            application=application,
            integration=integration,
            integration_type='version_control',
            is_active=False
        )

        data = {
            'integration_uuid': integration.uuid,
            'integration_type': 'version_control',
            'metadata': {'new_key': 'new_value'}
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_integration = serializer.save()

        assert app_integration.id == existing.id
        assert app_integration.metadata == {'new_key': 'new_value'}
        assert app_integration.is_active is True

    def test_create_with_tools(self):
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        data = {
            'integration_uuid': integration.uuid,
            'integration_type': 'version_control',
            'tools': {
                'github_version_control:list_commits': {'is_enabled': True},
                'github_version_control:list_pull_requests': {'is_enabled': False}
            }
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_integration = serializer.save()

        assert app_integration.tool_configs.filter(tool_id='github_version_control:list_commits', is_enabled=True).exists()
        assert app_integration.tool_configs.filter(tool_id='github_version_control:list_pull_requests', is_enabled=False).exists()

    def test_create_with_custom_tools(self):
        import uuid as uuid_lib
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        data = {
            'integration_uuid': integration.uuid,
            'integration_type': 'version_control',
            'custom_tools': [
                {'uuid': str(uuid_lib.uuid4()), 'is_enabled': True},
                {'uuid': str(uuid_lib.uuid4()), 'is_enabled': False}
            ]
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_integration = serializer.save()

    def test_create_without_metadata(self):
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        data = {
            'integration_uuid': integration.uuid,
            'integration_type': 'version_control'
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_integration = serializer.save()

        assert app_integration.metadata is None

    def test_create_without_tools(self):
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        data = {
            'integration_uuid': integration.uuid,
            'integration_type': 'version_control'
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_integration = serializer.save()

        assert app_integration.tool_configs.count() == 0

    def test_to_representation_uses_app_integration_serializer(self):
        user = UserFactory()
        application = ApplicationFactory()
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegration.objects.create(
            application=application,
            integration=integration,
            integration_type='version_control'
        )

        mock_request = Mock()
        mock_request.user = user

        serializer = AppIntegrationCreateSerializer(context={'request': mock_request, 'application': application})
        data = serializer.to_representation(app_integration)

        assert 'integration' in data
        assert 'integration_type' in data
