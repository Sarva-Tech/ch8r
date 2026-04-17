import pytest
from rest_framework import serializers

from core.models import Application, LLMModel
from core.serializers.application import (
    ApplicationCreateSerializer,
    ApplicationViewSerializer,
)
from core.tests.factories import UserFactory, ApplicationFactory


@pytest.mark.unit
class TestApplicationCreateSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        serializer = ApplicationCreateSerializer(application)
        data = serializer.data

        expected_fields = ['name']
        for field in expected_fields:
            assert field in data

    def test_create_with_name(self):
        user = UserFactory()
        data = {'name': 'Test Application'}

        serializer = ApplicationCreateSerializer(data=data)
        assert serializer.is_valid()
        application = serializer.save(owner=user)

        assert application.name == 'Test Application'
        assert application.owner == user

    def test_create_without_name(self):
        data = {}

        serializer = ApplicationCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors


@pytest.mark.unit
class TestApplicationViewSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        serializer = ApplicationViewSerializer(application)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'name', 'owner_id', 'owner', 'llm_models', 'app_integrations']
        for field in expected_fields:
            assert field in data

    def test_serialization_includes_nested_owner(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        serializer = ApplicationViewSerializer(application)
        data = serializer.data

        assert 'owner' in data
        assert data['owner']['id'] == user.id

    def test_serialization_includes_owner_id(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        serializer = ApplicationViewSerializer(application)
        data = serializer.data

        assert 'owner_id' in data
        assert data['owner_id'] == user.id

    def test_get_llm_models_returns_empty_list(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)

        serializer = ApplicationViewSerializer(application)
        llm_models = serializer.get_llm_models(application)

        assert llm_models == []

    def test_get_llm_models_returns_configured_models(self):
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

        from core.models.app_model import AppModel
        AppModel.objects.create(
            application=application,
            llm_model=llm_model
        )

        serializer = ApplicationViewSerializer(application)
        llm_models = serializer.get_llm_models(application)

        assert len(llm_models) == 1
        assert llm_models[0]['id'] == llm_model.id
        assert llm_models[0]['uuid'] == llm_model.uuid
        assert llm_models[0]['name'] == 'Test Model'
        assert llm_models[0]['model_name'] == 'test-model'
        assert llm_models[0]['model_type'] == 'text'
        assert llm_models[0]['is_default'] == llm_model.is_default

    def test_get_llm_models_returns_distinct_models(self):
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

        from core.models.app_model import AppModel
        AppModel.objects.create(
            application=application,
            llm_model=llm_model
        )
        AppModel.objects.create(
            application=application,
            llm_model=llm_model
        )

        serializer = ApplicationViewSerializer(application)
        llm_models = serializer.get_llm_models(application)

        assert len(llm_models) == 1
