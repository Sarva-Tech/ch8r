import pytest
from rest_framework import serializers
from unittest.mock import Mock, patch
import json

from core.models import Integration
from core.serializers.integration import (
    IntegrationSerializer,
    IntegrationViewSerializer,
    IntegrationCreateSerializer,
)
from core.tests.factories import UserFactory, IntegrationFactory


@pytest.mark.unit
class TestIntegrationSerializer:
    def test_serialization_excludes_credentials(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user)

        serializer = IntegrationSerializer(integration)
        data = serializer.data

        assert 'credentials' not in data

    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user)

        serializer = IntegrationSerializer(integration)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'name', 'provider', 'creator', 'metadata', 'created_at', 'updated_at', 'supported_types']
        for field in expected_fields:
            assert field in data

    def test_get_supported_types_for_supported_provider(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user, provider='github')

        serializer = IntegrationSerializer(integration)
        supported_types = serializer.get_supported_types(integration)

        assert isinstance(supported_types, list)

    def test_get_supported_types_for_unsupported_provider(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user, provider='unknown_provider')

        serializer = IntegrationSerializer(integration)
        supported_types = serializer.get_supported_types(integration)

        assert supported_types == []


@pytest.mark.unit
class TestIntegrationViewSerializer:

    def test_is_alias_of_integration_serializer(self):
        assert IntegrationViewSerializer == IntegrationSerializer


@pytest.mark.unit
class TestIntegrationCreateSerializer:

    def test_serialization_includes_expected_fields(self):
        serializer = IntegrationCreateSerializer()
        expected_fields = ['uuid', 'name', 'provider', 'token', 'creator']
        for field in expected_fields:
            assert field in serializer.fields

    def test_token_is_write_only(self):
        serializer = IntegrationCreateSerializer()
        assert serializer.fields['token'].write_only

    def test_token_is_required_on_create(self):
        serializer = IntegrationCreateSerializer()
        assert serializer.fields['token'].required

    def test_init_makes_token_optional_on_update(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user)

        serializer = IntegrationCreateSerializer(instance=integration)
        assert not serializer.fields['token'].required
        assert serializer.fields['token'].allow_blank

    def test_init_makes_provider_read_only_on_update(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user)

        serializer = IntegrationCreateSerializer(instance=integration)
        assert serializer.fields['provider'].read_only

    def test_validate_provider_supported(self):
        serializer = IntegrationCreateSerializer()
        result = serializer.validate_provider('github')

        assert result == 'github'

    def test_validate_provider_unsupported(self):
        serializer = IntegrationCreateSerializer()
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_provider('unsupported_provider')

        assert "not supported" in str(exc_info.value)

    def test_validate_with_token_and_supported_provider(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        with patch('core.serializers.integration.importlib.import_module') as mock_import:
            mock_validator = Mock(return_value=(True, None, {'account_id': '123'}))
            mock_module = Mock()
            mock_module.validate_token = mock_validator
            mock_import.return_value = mock_module

            serializer = IntegrationCreateSerializer(context={'request': mock_request})
            attrs = {
                'provider': 'github',
                'token': 'valid_token'
            }

            with patch('core.serializers.integration.SUPPORTED_INTEGRATIONS', [{'id': 'github', 'validate': 'module.validate_token'}]):
                result = serializer.validate(attrs)

            assert result == attrs

    def test_validate_with_invalid_token(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        with patch('core.serializers.integration.importlib.import_module') as mock_import:
            mock_validator = Mock(return_value=(False, 'Invalid token', None))
            mock_module = Mock()
            mock_module.validate_token = mock_validator
            mock_import.return_value = mock_module

            serializer = IntegrationCreateSerializer(context={'request': mock_request})
            attrs = {
                'provider': 'github',
                'token': 'invalid_token'
            }

            with patch('core.serializers.integration.SUPPORTED_INTEGRATIONS', [{'id': 'github', 'validate': 'module.validate_token'}]):
                result = serializer.validate(attrs)

            assert result == attrs
            assert hasattr(serializer, '_credential_error')
            assert serializer._credential_error == 'Invalid token'

    def test_create_stores_token_in_credentials(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        data = {
            'name': 'Test Integration',
            'provider': 'github',
            'token': 'test_token'
        }

        serializer = IntegrationCreateSerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        integration = serializer.save()

        credentials = json.loads(integration.credentials)
        assert credentials == {'token': 'test_token'}
        assert integration.creator == user

    def test_create_merges_account_metadata(self):
        user = UserFactory()
        mock_request = Mock()
        mock_request.user = user

        serializer = IntegrationCreateSerializer(context={'request': mock_request})
        serializer._account_metadata = {'account_id': '123', 'username': 'testuser'}

        data = {
            'name': 'Test Integration',
            'provider': 'github',
            'token': 'test_token'
        }

        serializer = IntegrationCreateSerializer(data=data, context={'request': mock_request})
        serializer._account_metadata = {'account_id': '123', 'username': 'testuser'}
        assert serializer.is_valid()
        integration = serializer.save()

        assert 'account' in integration.metadata
        assert integration.metadata['account'] == {'account_id': '123', 'username': 'testuser'}

    def test_update_with_new_token(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user)
        mock_request = Mock()
        mock_request.user = user

        data = {
            'token': 'new_token'
        }

        serializer = IntegrationCreateSerializer(instance=integration, data=data, partial=True, context={'request': mock_request})
        assert serializer.is_valid()
        updated = serializer.save()

        credentials = json.loads(updated.credentials)
        assert credentials == {'token': 'new_token'}

    def test_update_without_token(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user)
        original_credentials = integration.credentials
        mock_request = Mock()
        mock_request.user = user

        data = {
            'name': 'Updated Name'
        }

        serializer = IntegrationCreateSerializer(instance=integration, data=data, partial=True, context={'request': mock_request})
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.credentials == original_credentials

    def test_update_merges_account_metadata(self):
        user = UserFactory()
        integration = IntegrationFactory(creator=user)
        mock_request = Mock()
        mock_request.user = user

        data = {
            'token': 'new_token'
        }

        serializer = IntegrationCreateSerializer(instance=integration, data=data, partial=True, context={'request': mock_request})
        serializer._account_metadata = {'account_id': '456'}
        assert serializer.is_valid()
        updated = serializer.save()

        assert 'account' in updated.metadata
        assert updated.metadata['account'] == {'account_id': '456'}
