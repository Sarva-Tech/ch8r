import pytest
from rest_framework import status

from core.models import ApplicationAPIKey
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import UserFactory, ApplicationFactory


@pytest.mark.api
class TestApplicationAPIKeyAPI(BaseAPITestCase):
    def setUp(self):
        super().setUp()

    def test_delete_other_users_api_key(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        api_key_b = ApplicationAPIKey.objects.create(
            application=app_b,
            name="User B's Key",
            hashed_api_key="hashed_key",
            permissions=['read'],
            owner=user_b
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/applications/{app_b.uuid}/api-keys/{api_key_b.id}/'
        response = self.client.delete(detail_url)

        self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN])

        api_key_exists = ApplicationAPIKey.objects.filter(id=api_key_b.id).exists()
        self.assertTrue(api_key_exists)
