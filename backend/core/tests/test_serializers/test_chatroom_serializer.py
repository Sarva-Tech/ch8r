import pytest
from rest_framework import serializers
from unittest.mock import Mock

from core.models import ChatRoom, ChatroomParticipant
from core.serializers.chatroom import (
    ChatRoomViewSerializer,
    ChatRoomNameUpdateSerializer,
    ChatRoomWithMessagesSerializer,
    ChatroomParticipantSerializer,
    ChatRoomPreviewSerializer,
    ChatRoomDetailSerializer,
)
from core.tests.factories import UserFactory, ApplicationFactory, AIProviderFactory


@pytest.mark.unit
class TestChatRoomViewSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        ai_provider = AIProviderFactory(creator=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application,
            ai_provider=ai_provider,
            model='gpt-4'
        )

        serializer = ChatRoomViewSerializer(chatroom)
        data = serializer.data

        expected_fields = ['uuid', 'name', 'ai_provider', 'model']
        for field in expected_fields:
            assert field in data

    def test_serialization_includes_nested_ai_provider(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        ai_provider = AIProviderFactory(creator=user, name='Test Provider')
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application,
            ai_provider=ai_provider,
            model='gpt-4'
        )

        serializer = ChatRoomViewSerializer(chatroom)
        data = serializer.data

        assert 'ai_provider' in data


@pytest.mark.unit
class TestChatRoomNameUpdateSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )

        serializer = ChatRoomNameUpdateSerializer(chatroom)
        data = serializer.data

        expected_fields = ['name']
        for field in expected_fields:
            assert field in data

    def test_update_name(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Old Name',
            application=application
        )

        data = {'name': 'New Name'}
        serializer = ChatRoomNameUpdateSerializer(
            instance=chatroom,
            data=data,
            partial=True
        )
        assert serializer.is_valid()
        updated = serializer.save()

        assert updated.name == 'New Name'


@pytest.mark.unit
class TestChatroomParticipantSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )
        participant = ChatroomParticipant.objects.create(
            chatroom=chatroom,
            user_identifier='user123',
            role='user',
            metadata={'key': 'value'}
        )

        serializer = ChatroomParticipantSerializer(participant)
        data = serializer.data

        expected_fields = ['uuid', 'user_identifier', 'role', 'metadata']
        for field in expected_fields:
            assert field in data


@pytest.mark.unit
class TestChatRoomPreviewSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )

        serializer = ChatRoomPreviewSerializer(chatroom)
        data = serializer.data

        expected_fields = ['uuid', 'name', 'last_message', 'has_unread']
        for field in expected_fields:
            assert field in data

    def test_get_last_message_dashboard_user(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )

        serializer = ChatRoomPreviewSerializer(
            chatroom,
            context={'user_identifier': 'dashboard_user123'}
        )
        last_message = serializer.get_last_message(chatroom)

        assert last_message is None

    def test_get_last_message_widget_user_filters_internal(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )

        serializer = ChatRoomPreviewSerializer(
            chatroom,
            context={'user_identifier': 'widget_user123'}
        )
        last_message = serializer.get_last_message(chatroom)

        assert last_message is None

    def test_get_has_unread_with_participant(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )
        ChatroomParticipant.objects.create(
            chatroom=chatroom,
            user_identifier='user123',
            has_unread=True
        )

        serializer = ChatRoomPreviewSerializer(
            chatroom,
            context={'user_identifier': 'user123'}
        )
        has_unread = serializer.get_has_unread(chatroom)

        assert has_unread is True

    def test_get_has_unread_without_participant(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )

        serializer = ChatRoomPreviewSerializer(
            chatroom,
            context={'user_identifier': 'user123'}
        )
        has_unread = serializer.get_has_unread(chatroom)

        assert has_unread is False

    def test_get_has_unread_without_user_identifier(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )

        serializer = ChatRoomPreviewSerializer(chatroom)
        has_unread = serializer.get_has_unread(chatroom)

        assert has_unread is False


@pytest.mark.unit
class TestChatRoomWithMessagesSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        ai_provider = AIProviderFactory(creator=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application,
            ai_provider=ai_provider,
            model='gpt-4'
        )

        serializer = ChatRoomWithMessagesSerializer(chatroom)
        data = serializer.data

        expected_fields = ['uuid', 'name', 'application', 'messages', 'ai_provider', 'ai_model']
        for field in expected_fields:
            assert field in data

    def test_get_messages_uses_context_messages_qs(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )

        mock_messages_qs = Mock()
        mock_messages_qs.all.return_value = []
        mock_messages_qs.__iter__ = Mock(return_value=iter([]))
        serializer = ChatRoomWithMessagesSerializer(
            chatroom,
            context={'messages_qs': mock_messages_qs}
        )
        messages = serializer.get_messages(chatroom)

        assert messages == []


@pytest.mark.unit
class TestChatRoomDetailSerializer:
    def test_serialization_includes_expected_fields(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )

        serializer = ChatRoomDetailSerializer(chatroom)
        data = serializer.data

        expected_fields = ['uuid', 'name', 'participants', 'messages']
        for field in expected_fields:
            assert field in data

    def test_serialization_includes_nested_participants(self):
        user = UserFactory()
        application = ApplicationFactory(owner=user)
        chatroom = ChatRoom.objects.create(
            name='Test Chat',
            application=application
        )
        ChatroomParticipant.objects.create(
            chatroom=chatroom,
            user_identifier='user123',
            role='user'
        )

        serializer = ChatRoomDetailSerializer(chatroom)
        data = serializer.data

        assert 'participants' in data
        assert len(data['participants']) == 1
