import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from core.models import Application, AIProvider, AppAIProvider


class AppAIProviderTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='test')
        self.application = Application.objects.create(owner=self.user, name='Test App')
        self.ai_provider = AIProvider.objects.create(
            name='Test Provider',
            provider='openai',
            provider_api_key='test-key',
            metadata={'base_url': 'https://api.openai.com'},
            creator=self.user
        )

    def tearDown(self):
        AppAIProvider.objects.all().delete()

    def test_create_app_ai_provider(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('application-ai-providers-list', kwargs={'application_uuid': self.application.uuid})
        data = {
            'ai_provider_id': self.ai_provider.id,
            'context': 'widget',
            'capability': 'text',
            'external_model_id': 'gpt-4'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['context'], 'widget')
        self.assertEqual(response.data['capability'], 'text')
        self.assertEqual(response.data['priority'], 100)
        self.assertEqual(response.data['external_model_id'], 'gpt-4')
        self.assertEqual(response.data['ai_provider']['id'], self.ai_provider.id)

    def test_list_app_ai_providers(self):
        config = AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='widget',
            capability='text',
            external_model_id='gpt-4'
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('application-ai-providers-list', kwargs={'application_uuid': self.application.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], config.id)

    def test_filter_by_context(self):
        AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='widget',
            capability='text'
        )
        AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='dashboard',
            capability='text'
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('application-ai-providers-list', kwargs={'application_uuid': self.application.uuid})
        response = self.client.get(url, {'context': 'widget'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['context'], 'widget')

    def test_filter_by_capability(self):
        AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='widget',
            capability='text'
        )
        AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='widget',
            capability='image'
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('application-ai-providers-list', kwargs={'application_uuid': self.application.uuid})
        response = self.client.get(url, {'capability': 'text'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['capability'], 'text')

    def test_update_app_ai_provider(self):
        config = AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='widget',
            capability='text',
            external_model_id='gpt-4'
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('application-ai-providers-detail', kwargs={
            'application_uuid': self.application.uuid,
            'uuid': config.uuid
        })
        data = {'external_model_id': 'gpt-3.5-turbo'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        config.refresh_from_db()
        self.assertEqual(config.external_model_id, 'gpt-3.5-turbo')

    def test_delete_app_ai_provider(self):
        config = AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider
        )

        self.client.force_authenticate(user=self.user)
        url = reverse('application-ai-providers-detail', kwargs={
            'application_uuid': self.application.uuid,
            'uuid': config.uuid
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AppAIProvider.objects.filter(id=config.id).exists())

    def test_priority_auto_assignment(self):
        config1 = AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='widget',
            capability='text'
        )
        self.assertEqual(config1.priority, 100)

        config2 = AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='widget',
            capability='text'
        )
        self.assertEqual(config2.priority, 200)

        config3 = AppAIProvider.objects.create(
            application=self.application,
            ai_provider=self.ai_provider,
            context='dashboard',
            capability='text'
        )
        self.assertEqual(config3.priority, 100)

    def test_unauthorized_access(self):
        other_user = User.objects.create_user(username='other', password='other')
        other_app = Application.objects.create(owner=other_user, name='Other App')
        other_ai_provider = AIProvider.objects.create(
            name='Other AI Provider',
            provider='openai',
            provider_api_key='test',
            metadata={'base_url': 'https://api.openai.com'},
            creator=other_user
        )
        other_config = AppAIProvider.objects.create(
            application=other_app,
            ai_provider=other_ai_provider,
            context='widget',
            capability='text',
            external_model_id='gpt-4'
        )

        self.client.force_authenticate(user=self.user)

        url = reverse('application-ai-providers-list', kwargs={'application_uuid': other_app.uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        data = {
            'ai_provider_id': self.ai_provider.id,
            'context': 'widget',
            'capability': 'text',
            'external_model_id': 'gpt-4'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        update_url = reverse('application-ai-providers-detail', kwargs={
            'application_uuid': other_app.uuid,
            'uuid': other_config.uuid
        })
        update_data = {'external_model_id': 'gpt-3.5-turbo'}
        response = self.client.put(update_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(update_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_ai_provider(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('application-ai-providers-list', kwargs={'application_uuid': self.application.uuid})
        data = {
            'ai_provider_id': 999,
            'context': 'widget',
            'capability': 'text'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
