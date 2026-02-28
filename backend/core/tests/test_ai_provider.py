import pytest
from rest_framework import status
from rest_framework.test import APIClient

from core.models import AIProvider
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import UserFactory, AIProviderFactory


@pytest.mark.api
class TestAIProviderAPI(BaseAPITestCase):
    """Test suite for AI Provider API endpoints."""

    def setUp(self):
        super().setUp()
        self.list_url = '/api/ai-providers/'

    def test_list_ai_providers_authenticated_user(self):
        """Test that authenticated users can list their AI providers."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider1 = AIProviderFactory(creator=user, name="OpenAI Provider")
        provider2 = AIProviderFactory(creator=user, name="Anthropic Provider")

        other_user = UserFactory()
        other_provider = AIProviderFactory(creator=other_user, name="Other User Provider")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 2)

        provider_names = [provider['name'] for provider in data]
        self.assertIn("OpenAI Provider", provider_names)
        self.assertIn("Anthropic Provider", provider_names)
        self.assertNotIn("Other User Provider", provider_names)

        provider_data = data[0]
        expected_fields = ['id', 'uuid', 'name', 'provider', 'base_url', 'is_builtin', 'creator', 'created_at', 'updated_at']
        for field in expected_fields:
            self.assertIn(field, provider_data)

    def test_list_ai_providers_unauthenticated(self):
        """Test that unauthenticated users cannot list AI providers."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_other_users_provider(self):
        """Test that user A cannot retrieve user B's AI provider by ID."""
        user_a = UserFactory()
        user_b = UserFactory()

        provider_b = AIProviderFactory(creator=user_b, name="User B's Provider")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/ai-providers/{provider_b.id}/'
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_other_users_provider(self):
        """Test that user A cannot update user B's AI provider."""
        user_a = UserFactory()
        user_b = UserFactory()

        provider_b = AIProviderFactory(creator=user_b, name="User B's Provider")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/ai-providers/{provider_b.id}/'
        update_data = {'name': 'Hacked Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_other_users_provider(self):
        """Test that user A cannot delete user B's AI provider."""
        user_a = UserFactory()
        user_b = UserFactory()

        provider_b = AIProviderFactory(creator=user_b, name="User B's Provider")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/ai-providers/{provider_b.id}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_ai_provider(self):
        """Test that authenticated user can create their own AI provider."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        create_data = {
            'name': 'My OpenAI Provider',
            'provider': 'openai',
            'base_url': 'https://api.openai.com/v1',
            'provider_api_key': 'sk-test123456789'
        }

        response = self.client.post(self.list_url, create_data, format='json')

        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['name'], 'My OpenAI Provider')
        self.assertEqual(data['provider'], 'openai')
        self.assertEqual(data['base_url'], 'https://api.openai.com/v1')
        self.assertEqual(data['creator'], user.id)

        provider = AIProvider.objects.get(id=data['id'])
        self.assertEqual(provider.creator, user)
        self.assertEqual(provider.name, 'My OpenAI Provider')

    def test_update_own_provider(self):
        """Test that authenticated user can update their own AI provider."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, name="Original Name")

        detail_url = f'/api/ai-providers/{provider.id}/'
        update_data = {'name': 'Updated Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        print(response)
        self.assertEqual(data['name'], 'Updated Name')
        self.assertEqual(data['provider'], provider.provider)
        self.assertEqual(data['creator'], user.id)

        provider.refresh_from_db()
        self.assertEqual(provider.name, 'Updated Name')

    def test_cannot_update_provider_field(self):
        """Test that authenticated user cannot update the provider field of their AI provider."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, provider='openai', name="Original Name")

        detail_url = f'/api/ai-providers/{provider.id}/'
        update_data = {
            'name': 'Updated Name',
            'provider': 'anthropic'
        }
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        provider.refresh_from_db()
        self.assertEqual(provider.name, 'Updated Name')
        self.assertEqual(provider.provider, 'openai')

    def test_delete_own_provider(self):
        """Test that authenticated user can delete their own AI provider."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, name="Provider to Delete")

        detail_url = f'/api/ai-providers/{provider.id}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(AIProvider.DoesNotExist):
            AIProvider.objects.get(id=provider.id)
