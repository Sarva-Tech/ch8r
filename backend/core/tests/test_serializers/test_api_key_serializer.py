import pytest
from rest_framework import serializers
from unittest.mock import Mock, patch

from core.models import ApplicationAPIKey
from core.serializers.api_key import APIKeySerializer
from core.tests.factories import UserFactory, ApplicationFactory


@pytest.mark.unit
class TestAPIKeySerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory()
        api_key = ApplicationAPIKey(
            application=application,
            name="Test API Key",
            permissions=['read', 'write'],
            owner=user
        )

        serializer = APIKeySerializer(api_key)
        data = serializer.data

        expected_fields = ['name', 'permissions', 'id', 'created', 'owner']
        for field in expected_fields:
            assert field in data

    def test_serialization_excludes_api_key(self):
        user = UserFactory()
        application = ApplicationFactory()
        api_key = ApplicationAPIKey(
            application=application,
            name="Test API Key",
            permissions=['read'],
            owner=user
        )

        serializer = APIKeySerializer(api_key)
        data = serializer.data

        assert 'api_key' not in data
        assert 'hashed_api_key' not in data

    def test_permissions_field_validation_valid_choices(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read', 'write', 'delete']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()

    def test_permissions_field_validation_invalid_choice(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read', 'invalid_permission']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert not serializer.is_valid()
        assert 'permissions' in serializer.errors


@pytest.mark.unit
class TestAPIKeySerializerGenerateApiKey:
    def test_generate_api_key_returns_string(self):
        serializer = APIKeySerializer()
        api_key = serializer.generate_api_key()
        assert isinstance(api_key, str)

    def test_generate_api_key_length(self):
        serializer = APIKeySerializer()
        api_key = serializer.generate_api_key()
        assert len(api_key) > 0

    def test_generate_api_key_uniqueness(self):
        serializer = APIKeySerializer()
        api_key1 = serializer.generate_api_key()
        api_key2 = serializer.generate_api_key()
        assert api_key1 != api_key2


@pytest.mark.unit
class TestAPIKeySerializerCreate:
    def test_create_sets_owner_from_request(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        api_key_instance, api_key_raw = serializer.save()

        assert api_key_instance.owner == user

    def test_create_sets_application(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        api_key_instance, api_key_raw = serializer.save()

        assert api_key_instance.application == application

    def test_create_sets_name(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        api_key_instance, api_key_raw = serializer.save()

        assert api_key_instance.name == 'Test API Key'

    def test_create_sets_permissions(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read', 'write']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        api_key_instance, api_key_raw = serializer.save()

        assert api_key_instance.permissions == ['read', 'write']

    def test_create_returns_tuple(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        result = serializer.save()

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], ApplicationAPIKey)
        assert isinstance(result[1], str)

    def test_create_hashes_api_key(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        api_key_instance, api_key_raw = serializer.save()

        assert api_key_instance.hashed_api_key != api_key_raw
        assert api_key_instance.hashed_api_key is not None
        assert len(api_key_instance.hashed_api_key) > 0

    def test_create_invalid_application_uuid(self):
        from django.core.exceptions import ValidationError as DjangoValidationError

        user = UserFactory()

        data = {
            'name': 'Test API Key',
            'permissions': ['read']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': 'invalid-uuid'}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()

        with pytest.raises(DjangoValidationError):
            serializer.save()

    def test_create_with_all_permissions(self):
        user = UserFactory()
        application = ApplicationFactory()

        data = {
            'name': 'Full Access Key',
            'permissions': ['read', 'write', 'delete']
        }

        mock_request = Mock()
        mock_request.user = user
        mock_request.resolver_match = Mock()
        mock_request.resolver_match.kwargs = {'application_uuid': application.uuid}

        serializer = APIKeySerializer(data=data, context={'request': mock_request})
        assert serializer.is_valid()
        api_key_instance, api_key_raw = serializer.save()

        assert api_key_instance.permissions == ['read', 'write', 'delete']
