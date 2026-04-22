import pytest
from rest_framework import status

from core.models import AppModel
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import (
    UserFactory,
    ApplicationFactory,
    LLMModelFactory
)


@pytest.mark.api
class TestAppModelAPI(BaseAPITestCase):
    def setUp(self):
        super().setUp()

    def test_configure_models_other_users_application(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        llm_model_a = LLMModelFactory(owner=user_a, name="User A's Model")

        self.client.force_authenticate(user=user_a)

        url = f'/api/applications/{app_b.uuid}/models/'
        data = {
            'models': [
                {
                    'llm_model_id': llm_model_a.id
                }
            ]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        app_models_count = AppModel.objects.filter(application=app_b).count()
        self.assertEqual(app_models_count, 0)
