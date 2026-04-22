import pytest
from rest_framework import status

from core.models import KnowledgeBase
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import UserFactory, ApplicationFactory


@pytest.mark.api
class TestKnowledgeBaseAPI(BaseAPITestCase):
    def setUp(self):
        super().setUp()

    def test_list_knowledge_base_other_users_application(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        kb_b = KnowledgeBase.objects.create(
            application=app_b,
            source_type='text',
            path='test.txt',
            metadata={'content': 'test content'}
        )

        self.client.force_authenticate(user=user_a)

        list_url = f'/api/applications/{app_b.uuid}/knowledge-base/'
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_other_users_knowledge_base(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        kb_b = KnowledgeBase.objects.create(
            application=app_b,
            source_type='text',
            path='test.txt',
            metadata={'content': 'test content'}
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/knowledge-base/{kb_b.uuid}/'
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_other_users_knowledge_base(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        kb_b = KnowledgeBase.objects.create(
            application=app_b,
            source_type='text',
            path='test.txt',
            metadata={'content': 'test content'}
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/knowledge-base/{kb_b.uuid}/'
        update_data = {'content': 'Hacked content'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_other_users_knowledge_base(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        kb_b = KnowledgeBase.objects.create(
            application=app_b,
            source_type='text',
            path='test.txt',
            metadata={'content': 'test content'}
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/knowledge-base/{kb_b.uuid}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        kb_exists = KnowledgeBase.objects.filter(id=kb_b.id).exists()
        self.assertTrue(kb_exists)
