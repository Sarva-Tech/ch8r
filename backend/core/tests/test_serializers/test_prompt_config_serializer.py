import pytest
from rest_framework import serializers

from core.serializers.prompt_config import PromptConfigSerializer


@pytest.mark.unit
class TestPromptConfigSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = PromptConfigSerializer()
        expected_fields = ['tone', 'response_style', 'custom_instructions', 'role', 'behavior']
        for field in expected_fields:
            assert field in serializer.fields

    def test_tone_has_correct_choices(self):
        serializer = PromptConfigSerializer()
        expected_choices = ["professional", "friendly", "formal", "casual"]
        assert set(serializer.fields['tone'].choices) == set(expected_choices)

    def test_response_style_has_correct_choices(self):
        serializer = PromptConfigSerializer()
        expected_choices = ["balanced", "concise", "detailed", "step_by_step"]
        assert set(serializer.fields['response_style'].choices) == set(expected_choices)

    def test_custom_instructions_max_length(self):
        serializer = PromptConfigSerializer()
        assert serializer.fields['custom_instructions'].max_length == 1000

    def test_custom_instructions_allow_blank(self):
        serializer = PromptConfigSerializer()
        assert serializer.fields['custom_instructions'].allow_blank

    def test_custom_instructions_not_required(self):
        serializer = PromptConfigSerializer()
        assert not serializer.fields['custom_instructions'].required

    def test_custom_instructions_default(self):
        serializer = PromptConfigSerializer()
        assert serializer.fields['custom_instructions'].default == ""

    def test_role_max_length(self):
        serializer = PromptConfigSerializer()
        assert serializer.fields['role'].max_length == 200

    def test_role_not_allow_blank(self):
        serializer = PromptConfigSerializer()
        assert not serializer.fields['role'].allow_blank

    def test_role_not_required(self):
        serializer = PromptConfigSerializer()
        assert not serializer.fields['role'].required

    def test_role_default(self):
        serializer = PromptConfigSerializer()
        assert serializer.fields['role'].default == "customer service assistant"

    def test_behavior_max_length(self):
        serializer = PromptConfigSerializer()
        assert serializer.fields['behavior'].max_length == 500

    def test_behavior_not_allow_blank(self):
        serializer = PromptConfigSerializer()
        assert not serializer.fields['behavior'].allow_blank

    def test_behavior_not_required(self):
        serializer = PromptConfigSerializer()
        assert not serializer.fields['behavior'].required

    def test_behavior_default(self):
        serializer = PromptConfigSerializer()
        assert serializer.fields['behavior'].default == "answer user questions politely and competently"

    def test_validate_valid_tone(self):
        data = {
            'tone': 'professional',
            'response_style': 'balanced'
        }

        serializer = PromptConfigSerializer(data=data)
        assert serializer.is_valid()

    def test_validate_invalid_tone(self):
        data = {
            'tone': 'invalid_tone',
            'response_style': 'balanced'
        }

        serializer = PromptConfigSerializer(data=data)
        assert not serializer.is_valid()
        assert 'tone' in serializer.errors

    def test_validate_valid_response_style(self):
        data = {
            'tone': 'professional',
            'response_style': 'detailed'
        }

        serializer = PromptConfigSerializer(data=data)
        assert serializer.is_valid()

    def test_validate_invalid_response_style(self):
        data = {
            'tone': 'professional',
            'response_style': 'invalid_style'
        }

        serializer = PromptConfigSerializer(data=data)
        assert not serializer.is_valid()
        assert 'response_style' in serializer.errors

    def test_validate_with_all_fields(self):
        data = {
            'tone': 'friendly',
            'response_style': 'detailed',
            'custom_instructions': 'Be extra helpful',
            'role': 'support agent',
            'behavior': 'Provide detailed explanations'
        }

        serializer = PromptConfigSerializer(data=data)
        assert serializer.is_valid()

    def test_validate_custom_instructions_too_long(self):
        data = {
            'tone': 'professional',
            'response_style': 'balanced',
            'custom_instructions': 'x' * 1001
        }

        serializer = PromptConfigSerializer(data=data)
        assert not serializer.is_valid()
        assert 'custom_instructions' in serializer.errors

    def test_validate_role_too_long(self):
        data = {
            'tone': 'professional',
            'response_style': 'balanced',
            'role': 'x' * 201
        }

        serializer = PromptConfigSerializer(data=data)
        assert not serializer.is_valid()
        assert 'role' in serializer.errors

    def test_validate_behavior_too_long(self):
        data = {
            'tone': 'professional',
            'response_style': 'balanced',
            'behavior': 'x' * 501
        }

        serializer = PromptConfigSerializer(data=data)
        assert not serializer.is_valid()
        assert 'behavior' in serializer.errors
