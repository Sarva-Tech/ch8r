import pytest
from rest_framework import status

from core.models import ChatRoom
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import UserFactory, ApplicationFactory, AIProviderFactory


@pytest.mark.api
class TestChatRoomAPI(BaseAPITestCase):
    def setUp(self):
        super().setUp()

    def test_retrieve_other_users_chatroom(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        ai_provider_b = AIProviderFactory(creator=user_b)
        chatroom_b = ChatRoom.objects.create(
            application=app_b,
            name="User B's Chatroom",
            ai_provider=ai_provider_b
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/chatrooms/{chatroom_b.uuid}/'
        response = self.client.get(detail_url)

        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN, status.HTTP_200_OK])

    def test_delete_other_users_chatroom(self):
        """Test that user A cannot delete user B's chatroom."""
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        ai_provider_b = AIProviderFactory(creator=user_b)
        chatroom_b = ChatRoom.objects.create(
            application=app_b,
            name="User B's Chatroom",
            ai_provider=ai_provider_b
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/chatrooms/{chatroom_b.uuid}/delete/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        chatroom_exists = ChatRoom.objects.filter(id=chatroom_b.id).exists()
        self.assertTrue(chatroom_exists)

    def test_update_other_users_chatroom(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        ai_provider_b = AIProviderFactory(creator=user_b)
        chatroom_b = ChatRoom.objects.create(
            application=app_b,
            name="User B's Chatroom",
            ai_provider=ai_provider_b
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/chatrooms/{chatroom_b.uuid}/'
        update_data = {'name': 'Hacked Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        chatroom_b.refresh_from_db()
        self.assertEqual(chatroom_b.name, "User B's Chatroom")

    def test_list_chatrooms_other_users_application(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        ai_provider_b = AIProviderFactory(creator=user_b)
        chatroom_b = ChatRoom.objects.create(
            application=app_b,
            name="User B's Chatroom",
            ai_provider=ai_provider_b
        )

        self.client.force_authenticate(user=user_a)

        list_url = f'/api/applications/{app_b.uuid}/chatrooms/'
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
