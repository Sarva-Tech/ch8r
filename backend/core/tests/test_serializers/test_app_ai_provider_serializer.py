import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.models import AppAIProvider, AIProvider
from core.serializers.app_ai_provider import (
    AppAIProviderSerializer,
    AppAIProviderCreateSerializer,
    AppAIProviderUpdateSerializer,
)
from core.tests.factories import UserFactory, AIProviderFactory, ApplicationFactory


@pytest.mark.unit
class TestAppAIProviderSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user)
        app_ai_provider = AppAIProvider(
            application=application,
            ai_provider=ai_provider,
            context='test',
            capability='text',
            external_model_id='model-123'
        )

        serializer = AppAIProviderSerializer(app_ai_provider)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'ai_provider', 'context', 'capability', 'priority', 'external_model_id', 'is_active', 'created_at', 'updated_at']
        for field in expected_fields:
            assert field in data

    def test_serialization_includes_nested_ai_provider(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user, name='Test Provider')
        app_ai_provider = AppAIProvider(
            application=application,
            ai_provider=ai_provider,
            context='test',
            capability='text'
        )

        serializer = AppAIProviderSerializer(app_ai_provider)
        data = serializer.data

        assert 'ai_provider' in data
        assert data['ai_provider']['name'] == 'Test Provider'


@pytest.mark.unit
class TestAppAIProviderCreateSerializer:
    def test_validate_ai_provider_id_valid_owned_provider(self):
        user = UserFactory()
        ai_provider = AIProviderFactory(creator=user)

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderCreateSerializer(context={'request': mock_request})
        result = serializer.validate_ai_provider_id(ai_provider.id)

        assert result == ai_provider.id

    def test_validate_ai_provider_id_valid_builtin_provider(self):
        user = UserFactory()
        ai_provider = AIProviderFactory(creator=user, is_builtin=True)

        other_user = UserFactory()
        mock_request = Mock()
        mock_request.user = other_user

        serializer = AppAIProviderCreateSerializer(context={'request': mock_request})
        result = serializer.validate_ai_provider_id(ai_provider.id)

        assert result == ai_provider.id

    def test_validate_ai_provider_id_unowned_provider(self):
        user_a = UserFactory()
        user_b = UserFactory()
        ai_provider = AIProviderFactory(creator=user_a, is_builtin=False)

        mock_request = Mock()
        mock_request.user = user_b

        serializer = AppAIProviderCreateSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_ai_provider_id(ai_provider.id)

        assert "don't own this AI provider" in str(exc_info.value)

    def test_validate_ai_provider_id_not_found(self):
        user = UserFactory()

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderCreateSerializer(context={'request': mock_request})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_ai_provider_id(99999)

        assert "not found" in str(exc_info.value)

    def test_create_new_config(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user)

        data = {
            'ai_provider_id': ai_provider.id,
            'context': 'test',
            'capability': 'text',
            'external_model_id': 'model-123'
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_ai_provider = serializer.save()

        assert app_ai_provider.application == application
        assert app_ai_provider.ai_provider == ai_provider
        assert app_ai_provider.context == 'test'
        assert app_ai_provider.capability == 'text'
        assert app_ai_provider.external_model_id == 'model-123'

    def test_create_updates_existing_config(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider_old = AIProviderFactory(creator=user)
        ai_provider_new = AIProviderFactory(creator=user)

        existing_config = AppAIProvider.objects.create(
            application=application,
            ai_provider=ai_provider_old,
            context='test',
            capability='text',
            external_model_id='old-model'
        )

        data = {
            'ai_provider_id': ai_provider_new.id,
            'context': 'test',
            'capability': 'text',
            'external_model_id': 'new-model'
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_ai_provider = serializer.save()

        assert app_ai_provider.id == existing_config.id
        assert app_ai_provider.ai_provider == ai_provider_new
        assert app_ai_provider.external_model_id == 'new-model'

        assert AppAIProvider.objects.filter(application=application, context='test', capability='text').count() == 1

    def test_create_deletes_old_duplicates(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user)

        config1 = AppAIProvider.objects.create(
            application=application,
            ai_provider=ai_provider,
            context='test',
            capability='text',
            external_model_id='model-1'
        )
        config2 = AppAIProvider.objects.create(
            application=application,
            ai_provider=ai_provider,
            context='test',
            capability='text',
            external_model_id='model-2'
        )

        data = {
            'ai_provider_id': ai_provider.id,
            'context': 'test',
            'capability': 'text',
            'external_model_id': 'model-3'
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_ai_provider = serializer.save()

        assert AppAIProvider.objects.filter(application=application, context='test', capability='text').count() == 1

    def test_create_without_external_model_id(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user)

        data = {
            'ai_provider_id': ai_provider.id,
            'context': 'test',
            'capability': 'text'
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderCreateSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()
        app_ai_provider = serializer.save()

        assert app_ai_provider.external_model_id is None

    def test_to_representation_uses_app_ai_provider_serializer(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user)
        app_ai_provider = AppAIProvider.objects.create(
            application=application,
            ai_provider=ai_provider,
            context='test',
            capability='text'
        )

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderCreateSerializer(
            context={'request': mock_request, 'application': application}
        )
        data = serializer.to_representation(app_ai_provider)

        assert 'ai_provider' in data
        assert 'context' in data
        assert 'capability' in data


@pytest.mark.unit
class TestAppAIProviderUpdateSerializer:
    def test_update_external_model_id(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user)
        app_ai_provider = AppAIProvider.objects.create(
            application=application,
            ai_provider=ai_provider,
            context='test',
            capability='text',
            external_model_id='old-model'
        )

        data = {'external_model_id': 'new-model'}

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderUpdateSerializer(
            instance=app_ai_provider,
            data=data,
            partial=True,
            context={'request': mock_request}
        )
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.external_model_id == 'new-model'

    def test_update_without_external_model_id(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user)
        app_ai_provider = AppAIProvider.objects.create(
            application=application,
            ai_provider=ai_provider,
            context='test',
            capability='text',
            external_model_id='old-model'
        )

        data = {}

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderUpdateSerializer(
            instance=app_ai_provider,
            data=data,
            partial=True,
            context={'request': mock_request}
        )
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.external_model_id == 'old-model'

    def test_to_representation_uses_app_ai_provider_serializer(self):
        user = UserFactory()
        application = ApplicationFactory()
        ai_provider = AIProviderFactory(creator=user)
        app_ai_provider = AppAIProvider.objects.create(
            application=application,
            ai_provider=ai_provider,
            context='test',
            capability='text'
        )

        mock_request = Mock()
        mock_request.user = user

        serializer = AppAIProviderUpdateSerializer(context={'request': mock_request})
        data = serializer.to_representation(app_ai_provider)

        assert 'ai_provider' in data
        assert 'context' in data
        assert 'capability' in data
