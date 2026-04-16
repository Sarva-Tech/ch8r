import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.models import LLMModel
from core.serializers.llm_model import (
    LLMModelViewSerializer,
    LLMModelCreateSerializer,
)
from core.tests.factories import UserFactory


@pytest.mark.unit
class TestLLMModelViewSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type='text'
        )

        serializer = LLMModelViewSerializer(llm_model)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'name', 'base_url', 'model_name', 'model_type', 'is_default', 'created_at', 'owner']
        for field in expected_fields:
            assert field in data

    def test_serialization_excludes_api_key(self):
        user = UserFactory()
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type='text'
        )

        serializer = LLMModelViewSerializer(llm_model)
        data = serializer.data

        assert 'api_key' not in data


@pytest.mark.unit
class TestLLMModelCreateSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = LLMModelCreateSerializer()
        expected_fields = ['name', 'api_key', 'base_url', 'model_name', 'model_type']
        for field in expected_fields:
            assert field in serializer.fields

    def test_api_key_is_write_only(self):
        serializer = LLMModelCreateSerializer()
        assert serializer.fields['api_key'].write_only

    def test_api_key_is_optional(self):
        serializer = LLMModelCreateSerializer()
        assert not serializer.fields['api_key'].required
        assert serializer.fields['api_key'].allow_blank
        assert serializer.fields['api_key'].allow_null

    def test_create_with_api_key(self):
        user = UserFactory()
        data = {
            'name': 'Test Model',
            'api_key': 'test_api_key',
            'base_url': 'https://api.example.com',
            'model_name': 'gpt-4',
            'model_type': 'text'
        }

        serializer = LLMModelCreateSerializer(data=data)
        assert serializer.is_valid()
        llm_model = serializer.save(owner=user)

        assert llm_model.name == 'Test Model'
        assert llm_model.base_url == 'https://api.example.com'
        assert llm_model.model_name == 'gpt-4'
        assert llm_model.model_type == 'text'
        assert llm_model.config == 'test_api_key'

    def test_create_without_api_key(self):
        user = UserFactory()
        data = {
            'name': 'Test Model',
            'base_url': 'https://api.example.com',
            'model_name': 'gpt-4',
            'model_type': 'text'
        }

        serializer = LLMModelCreateSerializer(data=data)
        assert serializer.is_valid()
        llm_model = serializer.save(owner=user)

        assert llm_model.name == 'Test Model'
        assert llm_model.base_url == 'https://api.example.com'
        assert llm_model.model_name == 'gpt-4'
        assert llm_model.model_type == 'text'

    def test_update_with_api_key(self):
        user = UserFactory()
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type='text'
        )

        data = {
            'name': 'Updated Model',
            'api_key': 'new_api_key'
        }

        serializer = LLMModelCreateSerializer(instance=llm_model, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.name == 'Updated Model'
        assert updated.config == 'new_api_key'

    def test_update_without_api_key(self):
        user = UserFactory()
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type='text'
        )

        data = {
            'name': 'Updated Model'
        }

        serializer = LLMModelCreateSerializer(instance=llm_model, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.name == 'Updated Model'

    def test_update_with_null_api_key(self):
        user = UserFactory()
        llm_model = LLMModel.objects.create(
            owner=user,
            name='Test Model',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type='text'
        )

        data = {
            'api_key': None
        }

        serializer = LLMModelCreateSerializer(instance=llm_model, data=data, partial=True)
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.config == {} or updated.config == ''
