import pytest
from rest_framework import serializers

from core.models import Message
from core.serializers.message import (
    CreateMessageSerializer,
    ViewMessageSerializer,
)
from core.tests.factories import UserFactory, ApplicationFactory, AIProviderFactory


@pytest.mark.unit
class TestCreateMessageSerializer:
    def test_serialization_includes_expected_fields(self):
        serializer = CreateMessageSerializer()
        expected_fields = ['chatroom_identifier', 'sender_identifier', 'message', 'metadata', 'is_internal', 'ai_mode', 'ai_provider', 'model']
        for field in expected_fields:
            assert field in serializer.fields

    def test_chatroom_identifier_is_optional(self):
        serializer = CreateMessageSerializer()
        assert not serializer.fields['chatroom_identifier'].required

    def test_sender_identifier_is_optional(self):
        serializer = CreateMessageSerializer()
        assert not serializer.fields['sender_identifier'].required

    def test_message_is_required(self):
        serializer = CreateMessageSerializer()
        assert serializer.fields['message'].required

    def test_metadata_is_optional(self):
        serializer = CreateMessageSerializer()
        assert not serializer.fields['metadata'].required

    def test_is_internal_has_default(self):
        serializer = CreateMessageSerializer()
        assert serializer.fields['is_internal'].default == False

    def test_ai_mode_has_default(self):
        serializer = CreateMessageSerializer()
        assert serializer.fields['ai_mode'].default == False

    def test_ai_provider_is_optional(self):
        serializer = CreateMessageSerializer()
        assert not serializer.fields['ai_provider'].required

    def test_model_is_optional(self):
        serializer = CreateMessageSerializer()
        assert not serializer.fields['model'].required

    def test_init_sets_app_owner(self):
        user = UserFactory()
        serializer = CreateMessageSerializer(app_owner=user)
        assert serializer.app_owner == user

    def test_validate_ai_provider_valid(self):
        user = UserFactory()
        ai_provider = AIProviderFactory(creator=user)

        serializer = CreateMessageSerializer(app_owner=user)
        result = serializer.validate_ai_provider(ai_provider.id)

        assert result == ai_provider.id

    def test_validate_ai_provider_invalid(self):
        user = UserFactory()
        other_user = UserFactory()
        ai_provider = AIProviderFactory(creator=other_user)

        serializer = CreateMessageSerializer(app_owner=user)
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_ai_provider(ai_provider.id)

        assert "Invalid AI provider" in str(exc_info.value)

    def test_validate_ai_provider_none(self):
        user = UserFactory()

        serializer = CreateMessageSerializer(app_owner=user)
        result = serializer.validate_ai_provider(None)

        assert result is None


@pytest.mark.unit
class TestViewMessageSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        from core.models import ChatRoom
        chatroom = ChatRoom.objects.create(application=application, name='Test Chat')
        message = Message.objects.create(
            chatroom=chatroom,
            message='Test message',
            sender_identifier='user123'
        )

        serializer = ViewMessageSerializer(message)
        data = serializer.data

        expected_fields = ['id', 'uuid', 'sender_identifier', 'chatroom_identifier', 'message', 'metadata', 'ai_provider_id', 'model', 'is_internal', 'platform', 'ai_mode', 'created_at']
        for field in expected_fields:
            assert field in data

    def test_chatroom_identifier_is_uuid(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        from core.models import ChatRoom
        chatroom = ChatRoom.objects.create(application=application, name='Test Chat')
        message = Message.objects.create(
            chatroom=chatroom,
            message='Test message',
            sender_identifier='user123'
        )

        serializer = ViewMessageSerializer(message)
        data = serializer.data

        assert 'chatroom_identifier' in data
        assert data['chatroom_identifier'] == str(chatroom.uuid)
