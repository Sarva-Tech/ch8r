import pytest
from rest_framework import status

from core.models import Application
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import UserFactory, ApplicationFactory


@pytest.mark.api
class TestApplicationAPI(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = '/api/applications/'

    def test_list_applications_authenticated_user(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        app1 = ApplicationFactory(owner=user, name="App 1")
        app2 = ApplicationFactory(owner=user, name="App 2")

        other_user = UserFactory()
        other_app = ApplicationFactory(owner=other_user, name="Other App")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['results']), 2)

        app_names = [app['name'] for app in data['results']]
        self.assertIn("App 1", app_names)
        self.assertIn("App 2", app_names)
        self.assertNotIn("Other App", app_names)

    def test_list_applications_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_other_users_application(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/'
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_other_users_application(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/'
        update_data = {'name': 'Hacked Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_other_users_application(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_application(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        create_data = {
            'name': 'My Application',
        }

        response = self.client.post(self.list_url, create_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['name'], 'My Application')
        self.assertEqual(data['owner']['id'], user.id)

        app = Application.objects.get(uuid=data['uuid'])
        self.assertEqual(app.owner, user)
        self.assertEqual(app.name, 'My Application')

    def test_delete_own_application(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        app = ApplicationFactory(owner=user, name="App to Delete")

        detail_url = f'/api/applications/{app.uuid}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.assertRaises(Application.DoesNotExist):
            Application.objects.get(id=app.id)
