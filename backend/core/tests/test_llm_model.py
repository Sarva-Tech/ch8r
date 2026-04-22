import pytest
from rest_framework import status

from core.models import LLMModel
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import UserFactory


@pytest.mark.api
class TestLLMModelAPI(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.list_url = '/api/models/'

    def test_list_llm_models_authenticated_user(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        model1 = LLMModel.objects.create(
            owner=user,
            name='My Model 1',
            api_key='sk-test1',
            api_key_preview='sk-****1',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type=LLMModel.ModelType.TEXT
        )
        model2 = LLMModel.objects.create(
            owner=user,
            name='My Model 2',
            api_key='sk-test2',
            api_key_preview='sk-****2',
            base_url='https://api.example.com',
            model_name='gpt-3.5-turbo',
            model_type=LLMModel.ModelType.TEXT
        )

        other_user = UserFactory()
        other_model = LLMModel.objects.create(
            owner=other_user,
            name='Other Model',
            api_key='sk-test3',
            api_key_preview='sk-****3',
            base_url='https://api.example.com',
            model_name='claude-3',
            model_type=LLMModel.ModelType.TEXT
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        model_names = [model['name'] for model in data['results']]
        self.assertIn("My Model 1", model_names)
        self.assertIn("My Model 2", model_names)
        self.assertNotIn("Other Model", model_names)

    def test_list_llm_models_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_other_users_llm_model(self):
        user_a = UserFactory()
        user_b = UserFactory()

        model_b = LLMModel.objects.create(
            owner=user_b,
            name="User B's Model",
            api_key='sk-test',
            api_key_preview='sk-****',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type=LLMModel.ModelType.TEXT
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/models/{model_b.uuid}/'
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_other_users_llm_model(self):
        user_a = UserFactory()
        user_b = UserFactory()

        model_b = LLMModel.objects.create(
            owner=user_b,
            name="User B's Model",
            api_key='sk-test',
            api_key_preview='sk-****',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type=LLMModel.ModelType.TEXT
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/models/{model_b.uuid}/'
        update_data = {'name': 'Hacked Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_other_users_llm_model(self):
        user_a = UserFactory()
        user_b = UserFactory()

        model_b = LLMModel.objects.create(
            owner=user_b,
            name="User B's Model",
            api_key='sk-test',
            api_key_preview='sk-****',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type=LLMModel.ModelType.TEXT
        )

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/models/{model_b.uuid}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_llm_model(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        create_data = {
            'name': 'My LLM Model',
            'api_key': 'sk-test123456789',
            'base_url': 'https://api.openai.com',
            'model_name': 'gpt-4',
            'model_type': 'text'
        }

        response = self.client.post(self.list_url, create_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['name'], 'My LLM Model')
        self.assertEqual(data['owner'], user.id)

        model = LLMModel.objects.get(uuid=data['uuid'])
        self.assertEqual(model.owner, user)
        self.assertEqual(model.name, 'My LLM Model')

    def test_update_own_llm_model(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        model = LLMModel.objects.create(
            owner=user,
            name="Original Name",
            api_key='sk-test',
            api_key_preview='sk-****',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type=LLMModel.ModelType.TEXT
        )

        detail_url = f'/api/models/{model.uuid}/'
        update_data = {'name': 'Updated Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['name'], 'Updated Name')

        model.refresh_from_db()
        self.assertEqual(model.name, 'Updated Name')

    def test_delete_own_llm_model(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        model = LLMModel.objects.create(
            owner=user,
            name="Model to Delete",
            api_key='sk-test',
            api_key_preview='sk-****',
            base_url='https://api.example.com',
            model_name='gpt-4',
            model_type=LLMModel.ModelType.TEXT
        )

        detail_url = f'/api/models/{model.uuid}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.assertRaises(LLMModel.DoesNotExist):
            LLMModel.objects.get(id=model.id)
