import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.models import AppModel, LLMModel
from core.serializers.app_model import (
    AppModelViewSerializer,
    ConfigureAppModelSerializer,
    ConfigureAppModelsSerializer,
)
from core.tests.factories import UserFactory, ApplicationFactory


@pytest.mark.unit
class TestAppModelViewSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory()
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text'
        )
        app_model = AppModel(
            application=application,
            llm_model=llm_model
        )

        serializer = AppModelViewSerializer(app_model)
        data = serializer.data

        assert data['name'] == 'Test Model'
        assert data['model_name'] == 'test-model'

    def test_serialization_includes_nested_llm_model(self):
        user = UserFactory()
        application = ApplicationFactory()
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text'
        )
        app_model = AppModel(
            application=application,
            llm_model=llm_model
        )

        serializer = AppModelViewSerializer(app_model)
        data = serializer.data

        assert data['name'] == 'Test Model'
        assert data['model_type'] == 'text'

    def test_to_representation_returns_llm_model_data(self):
        user = UserFactory()
        application = ApplicationFactory()
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text'
        )
        app_model = AppModel(
            application=application,
            llm_model=llm_model
        )

        serializer = AppModelViewSerializer(app_model)
        data = serializer.to_representation(app_model)

        assert data['name'] == 'Test Model'
        assert 'application' not in data


@pytest.mark.unit
class TestConfigureAppModelSerializer:
    def test_get_fields_filters_queryset_for_user(self):
        user = UserFactory()
        user_model = LLMModel.objects.create(
            owner=user,
            name='User Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='user-model',
            model_type='text',
            is_default=False
        )
        other_user = UserFactory()
        other_model = LLMModel.objects.create(
            owner=other_user,
            name='Other Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='other-model',
            model_type='text',
            is_default=False
        )
        default_model = LLMModel.objects.create(
            owner=user,
            name='Default Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='default-model',
            model_type='text',
            is_default=True
        )

        mock_request = Mock()
        mock_request.user = user

        serializer = ConfigureAppModelSerializer(context={'request': mock_request})
        fields = serializer.get_fields()

        assert user_model in fields['llm_model'].queryset
        assert default_model in fields['llm_model'].queryset
        assert other_model not in fields['llm_model'].queryset

    def test_get_fields_returns_empty_queryset_for_no_user(self):
        mock_request = Mock()
        mock_request.user = None

        serializer = ConfigureAppModelSerializer(context={'request': mock_request})
        fields = serializer.get_fields()

        assert fields['llm_model'].queryset.count() == 0

    def test_validate_model_type_matches(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text'
        )

        attrs = {
            'model_type': 'text',
            'llm_model': llm_model
        }

        serializer = ConfigureAppModelSerializer(context={'application': application})
        result = serializer.validate(attrs)

        assert result == attrs

    def test_validate_model_type_mismatch(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text'
        )

        attrs = {
            'model_type': 'embedding',
            'llm_model': llm_model
        }

        serializer = ConfigureAppModelSerializer(context={'application': application})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate(attrs)

        assert "does not match" in str(exc_info.value)

    def test_validate_llm_model_owner_matches_application_owner(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text',
            is_default=False
        )

        serializer = ConfigureAppModelSerializer(context={'application': application})
        result = serializer.validate_llm_model(llm_model)

        assert result == llm_model

    def test_validate_llm_model_default_model_allowed(self):
        user_a = UserFactory()
        user_b = UserFactory()
        application = ApplicationFactory(owner=user_a)
        llm_model = LLMModel.objects.create(
            owner=user_b,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text',
            is_default=True
        )

        serializer = ConfigureAppModelSerializer(context={'application': application})
        result = serializer.validate_llm_model(llm_model)

        assert result == llm_model

    def test_validate_llm_model_owner_mismatch(self):
        user_a = UserFactory()
        user_b = UserFactory()
        application = ApplicationFactory(owner=user_a)
        llm_model = LLMModel.objects.create(
            owner=user_b,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text',
            is_default=False
        )

        serializer = ConfigureAppModelSerializer(context={'application': application})
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_llm_model(llm_model)

        assert "owner mismatch" in str(exc_info.value)


@pytest.mark.unit
class TestConfigureAppModelsSerializer:
    def test_serializer_accepts_list_of_models(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text'
        )

        data = {
            'models': [
                {
                    'model_type': 'text',
                    'llm_model': str(llm_model.uuid)
                }
            ]
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = ConfigureAppModelsSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()

    def test_serializer_accepts_empty_list(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        data = {'models': []}

        mock_request = Mock()
        mock_request.user = user

        serializer = ConfigureAppModelsSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert serializer.is_valid()

    def test_serializer_validates_each_model(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            api_key='test-key',
            api_key_preview='test***',
            base_url='https://example.com',
            model_name='test-model',
            model_type='text'
        )

        data = {
            'models': [
                {
                    'model_type': 'text',
                    'llm_model': str(llm_model.uuid)
                },
                {
                    'model_type': 'embedding',
                    'llm_model': str(llm_model.uuid)
                }
            ]
        }

        mock_request = Mock()
        mock_request.user = user

        serializer = ConfigureAppModelsSerializer(
            data=data,
            context={'request': mock_request, 'application': application}
        )
        assert not serializer.is_valid()
        assert 'models' in serializer.errors
