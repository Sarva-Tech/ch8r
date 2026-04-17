import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.models import AIProvider
from core.serializers.ai_provider import (
    AIProviderSerializer,
    AIProviderCreateSerializer,
)
from core.tests.factories import UserFactory, AIProviderFactory


@pytest.mark.unit
class TestAIProviderSerializer:

    def test_serialization_excludes_provider_api_key(self):
        user = UserFactory()
        provider = AIProviderFactory(
            creator=user,
            name="Test Provider",
            provider="gemini",
            provider_api_key="secret-key-123"
        )

        serializer = AIProviderSerializer(provider)
        data = serializer.data

        assert 'provider_api_key' not in data
        assert data['name'] == "Test Provider"
        assert data['provider'] == "gemini"

    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        provider = AIProviderFactory(
            creator=user,
            name="Test Provider",
            provider="gemini"
        )

        serializer = AIProviderSerializer(provider)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'name', 'provider', 'is_builtin', 'creator', 'created_at', 'updated_at', 'metadata']
        for field in expected_fields:
            assert field in data


@pytest.mark.unit
class TestAIProviderCreateSerializerInit:
    def test_init_without_instance(self):
        user = UserFactory()
        data = {
            'name': 'Test Provider',
            'provider': 'gemini',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})

        assert serializer.fields['provider_api_key'].required
        assert not serializer.fields['provider_api_key'].allow_blank
        assert not serializer.fields['provider'].read_only

    def test_init_with_instance(self):
        user = UserFactory()
        provider = AIProviderFactory(creator=user, provider="gemini")

        serializer = AIProviderCreateSerializer(
            instance=provider,
            data={'name': 'Updated Name'},
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )

        assert not serializer.fields['provider_api_key'].required
        assert serializer.fields['provider_api_key'].allow_blank
        assert serializer.fields['provider'].read_only


@pytest.mark.unit
class TestAIProviderCreateSerializerValidateProvider:
    def test_validate_provider_valid(self):
        serializer = AIProviderCreateSerializer()
        result = serializer.validate_provider('gemini')
        assert result == 'gemini'

    def test_validate_provider_invalid(self):
        serializer = AIProviderCreateSerializer()
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_provider('invalid_provider')

        assert "not supported" in str(exc_info.value)
        assert "Google Gemini" in str(exc_info.value)


@pytest.mark.unit
class TestAIProviderCreateSerializerValidate:
    def test_validate_gemini_provider_with_base_url(self):
        user = UserFactory()
        data = {
            'name': 'Gemini Provider',
            'provider': 'gemini',
            'base_url': 'https://api.example.com',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})
        assert serializer.is_valid()

    def test_validate_gemini_provider_without_base_url_on_create(self):
        user = UserFactory()
        data = {
            'name': 'Gemini Provider',
            'provider': 'gemini',
            'base_url': '',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})
        assert serializer.is_valid()

    def test_validate_gemini_provider_with_none_base_url_on_create(self):
        user = UserFactory()
        data = {
            'name': 'Gemini Provider',
            'provider': 'gemini',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})
        assert serializer.is_valid()

    def test_validate_gemini_provider_with_whitespace_base_url_on_create(self):
        user = UserFactory()
        data = {
            'name': 'Gemini Provider',
            'provider': 'gemini',
            'base_url': '   ',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})
        assert serializer.is_valid()

    def test_validate_gemini_provider_without_base_url_on_update(self):
        user = UserFactory()
        provider = AIProviderFactory(creator=user, provider='gemini')

        data = {'base_url': ''}
        serializer = AIProviderCreateSerializer(
            instance=provider,
            data=data,
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )
        assert serializer.is_valid()

    def test_validate_non_custom_provider_without_base_url(self):
        user = UserFactory()
        data = {
            'name': 'Gemini Provider',
            'provider': 'gemini',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})
        assert serializer.is_valid()

    def test_validate_gemini_provider_with_base_url_on_update(self):
        user = UserFactory()
        provider = AIProviderFactory(creator=user, provider='gemini')

        data = {'base_url': 'https://api.example.com/v2'}
        serializer = AIProviderCreateSerializer(
            instance=provider,
            data=data,
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )
        assert serializer.is_valid()


@pytest.mark.unit
class TestAIProviderCreateSerializerCreate:
    def test_create_sets_creator_from_request(self):
        user = UserFactory()
        data = {
            'name': 'Test Provider',
            'provider': 'gemini',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})
        assert serializer.is_valid()
        provider = serializer.save()

        assert provider.creator == user

    def test_create_extracts_metadata(self):
        user = UserFactory()
        data = {
            'name': 'Test Provider',
            'provider': 'gemini',
            'base_url': 'https://api.example.com',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})
        assert serializer.is_valid()
        provider = serializer.save()

        assert 'base_url' in provider.metadata
        assert provider.metadata['base_url'] == 'https://api.example.com'

    def test_create_without_base_url(self):
        user = UserFactory()
        data = {
            'name': 'Test Provider',
            'provider': 'gemini',
            'provider_api_key': 'test-key-123'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})
        assert serializer.is_valid()
        provider = serializer.save()

        assert provider.name == 'Test Provider'
        assert provider.provider == 'gemini'


@pytest.mark.unit
class TestAIProviderCreateSerializerUpdate:
    def test_update_with_new_api_key(self):
        user = UserFactory()
        provider = AIProviderFactory(creator=user, provider_api_key='old-key-123')

        data = {'provider_api_key': 'new-key-456'}
        serializer = AIProviderCreateSerializer(
            instance=provider,
            data=data,
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )
        assert serializer.is_valid()
        updated_provider = serializer.save()

        assert updated_provider.provider_api_key == 'new-key-456'

    def test_update_without_api_key_preserves_existing(self):
        user = UserFactory()
        provider = AIProviderFactory(creator=user, provider_api_key='existing-key-123')

        data = {'name': 'Updated Name'}
        serializer = AIProviderCreateSerializer(
            instance=provider,
            data=data,
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )
        assert serializer.is_valid()
        updated_provider = serializer.save()

        assert updated_provider.provider_api_key == 'existing-key-123'

    def test_update_with_empty_api_key_preserves_existing(self):
        user = UserFactory()
        provider = AIProviderFactory(creator=user, provider_api_key='existing-key-123')

        data = {'provider_api_key': ''}
        serializer = AIProviderCreateSerializer(
            instance=provider,
            data=data,
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )
        assert serializer.is_valid()
        updated_provider = serializer.save()

        assert updated_provider.provider_api_key == 'existing-key-123'

    def test_update_with_whitespace_api_key_preserves_existing(self):
        user = UserFactory()
        provider = AIProviderFactory(creator=user, provider_api_key='existing-key-123')

        data = {'provider_api_key': '   '}
        serializer = AIProviderCreateSerializer(
            instance=provider,
            data=data,
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )
        assert serializer.is_valid()
        updated_provider = serializer.save()

        assert updated_provider.provider_api_key == 'existing-key-123'

    def test_update_merges_metadata(self):
        user = UserFactory()
        provider = AIProviderFactory(
            creator=user,
            metadata={'old_field': 'old_value', 'name': 'Old Name'}
        )

        data = {'base_url': 'https://new-api.com'}
        serializer = AIProviderCreateSerializer(
            instance=provider,
            data=data,
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )
        assert serializer.is_valid()
        updated_provider = serializer.save()

        assert updated_provider.metadata['base_url'] == 'https://new-api.com'
        assert updated_provider.metadata['old_field'] == 'old_value'
        assert updated_provider.metadata['name'] == 'Old Name'

    def test_update_name(self):
        user = UserFactory()
        provider = AIProviderFactory(creator=user, name='Old Name')

        data = {'name': 'New Name'}
        serializer = AIProviderCreateSerializer(
            instance=provider,
            data=data,
            partial=True,
            context={'request': type('MockRequest', (), {'user': user})()}
        )
        assert serializer.is_valid()
        updated_provider = serializer.save()

        assert updated_provider.name == 'New Name'
