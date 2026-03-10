import pytest
from rest_framework import status
from unittest.mock import patch

from core.models import AIProvider
from core.serializers.ai_provider import AIProviderCreateSerializer
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
        self.assertEqual(len(data['results']), 2)

        provider_names = [provider['name'] for provider in data['results']]
        self.assertIn("OpenAI Provider", provider_names)
        self.assertIn("Anthropic Provider", provider_names)
        self.assertNotIn("Other User Provider", provider_names)

        provider_data = data['results'][0]
        expected_fields = ['id', 'uuid', 'name', 'provider', 'is_builtin', 'creator', 'created_at', 'updated_at', 'metadata']
        for field in expected_fields:
            self.assertIn(field, provider_data)

        self.assertIn('supported_ai_providers', data)
        self.assertIsInstance(data['supported_ai_providers'], list)

    def test_list_ai_providers_includes_builtin_and_user_owned(self):
        """Test that authenticated users can list their AI providers plus builtin providers."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        user_provider1 = AIProviderFactory(creator=user, name="User OpenAI Provider", is_builtin=False)
        user_provider2 = AIProviderFactory(creator=user, name="User Anthropic Provider", is_builtin=False)

        builtin_provider1 = AIProviderFactory(creator=user, name="Builtin OpenAI", is_builtin=True)
        builtin_provider2 = AIProviderFactory(creator=user, name="Builtin Claude", is_builtin=True)

        other_user = UserFactory()
        other_user_provider = AIProviderFactory(creator=other_user, name="Other User Provider", is_builtin=False)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['results']), 4)

        provider_names = [provider['name'] for provider in data['results']]
        self.assertIn("User OpenAI Provider", provider_names)
        self.assertIn("User Anthropic Provider", provider_names)
        self.assertIn("Builtin OpenAI", provider_names)
        self.assertIn("Builtin Claude", provider_names)
        self.assertNotIn("Other User Provider", provider_names)

        builtin_providers = [p for p in data['results'] if p['is_builtin']]
        user_owned_providers = [p for p in data['results'] if not p['is_builtin']]

        self.assertEqual(len(builtin_providers), 2)
        self.assertEqual(len(user_owned_providers), 2)

        builtin_names = [p['name'] for p in builtin_providers]
        self.assertIn("Builtin OpenAI", builtin_names)
        self.assertIn("Builtin Claude", builtin_names)

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

        detail_url = f'/api/ai-providers/{provider_b.uuid}/'
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_other_users_provider(self):
        """Test that user A cannot update user B's AI provider."""
        user_a = UserFactory()
        user_b = UserFactory()

        provider_b = AIProviderFactory(creator=user_b, name="User B's Provider")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/ai-providers/{provider_b.uuid}/'
        update_data = {'name': 'Hacked Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_other_users_provider(self):
        """Test that user A cannot delete user B's AI provider."""
        user_a = UserFactory()
        user_b = UserFactory()

        provider_b = AIProviderFactory(creator=user_b, name="User B's Provider")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/ai-providers/{provider_b.uuid}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider')
    def test_create_ai_provider(self, mock_validate):
        """Test that authenticated user can create their own AI provider."""
        mock_validate.return_value = (True, ['gemini-1.5-pro', 'gemini-1.5-flash'])
        
        user = UserFactory()
        self.client.force_authenticate(user=user)

        create_data = {
            'name': 'My Gemini Provider',
            'provider': 'gemini',
            'base_url': 'https://generativelanguage.googleapis.com',
            'provider_api_key': 'sk-test123456789'
        }

        response = self.client.post(self.list_url, create_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['ai_provider']['name'], 'My Gemini Provider')
        self.assertEqual(data['ai_provider']['provider'], 'gemini')
        self.assertEqual(data['ai_provider']['metadata']['base_url'], 'https://generativelanguage.googleapis.com')
        self.assertEqual(data['ai_provider']['creator'], user.id)
        self.assertTrue(data['validation']['is_valid'])
        self.assertEqual(data['validation']['models'], ['gemini-1.5-pro', 'gemini-1.5-flash'])

        provider = AIProvider.objects.get(uuid=data['ai_provider']['uuid'])
        self.assertEqual(provider.creator, user)
        self.assertEqual(provider.name, 'My Gemini Provider')
        self.assertEqual(provider.metadata['base_url'], 'https://generativelanguage.googleapis.com')

    @patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider')
    def test_update_own_provider(self, mock_validate):
        """Test that authenticated user can update their own AI provider."""
        mock_validate.return_value = (True, ['gemini-1.5-pro', 'gemini-1.5-flash'])
        
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, name="Original Name")

        detail_url = f'/api/ai-providers/{provider.uuid}/'
        update_data = {'name': 'Updated Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['name'], 'Updated Name')
        self.assertEqual(data['creator'], user.id)

        provider.refresh_from_db()
        self.assertEqual(provider.name, 'Updated Name')

    def test_cannot_update_provider_field(self):
        """Test that authenticated user cannot update the provider field of their AI provider."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, provider='openai', name="Original Name")

        detail_url = f'/api/ai-providers/{provider.uuid}/'
        update_data = {
            'name': 'Updated Name',
            'provider': 'anthropic'
        }
        with patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider') as mock_validate:
            mock_validate.return_value = (True, ['gpt-3.5-turbo'])
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

        detail_url = f'/api/ai-providers/{provider.uuid}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.assertRaises(AIProvider.DoesNotExist):
            AIProvider.objects.get(id=provider.id)

    def test_update_without_api_key_does_not_change_api_key(self):
        """Test that update request without specifying provider api key does not update provider api key."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, name="Test Provider")
        original_api_key = provider.provider_api_key

        detail_url = f'/api/ai-providers/{provider.uuid}/'
        update_data = {'name': 'Updated Name'}
        with patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider') as mock_validate:
            mock_validate.return_value = (True, ['gpt-3.5-turbo'])
            response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        provider.refresh_from_db()
        self.assertEqual(provider.name, 'Updated Name')
        self.assertEqual(provider.provider_api_key, original_api_key)

    @patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider')
    def test_update_with_api_key_changes_api_key(self, mock_validate):
        """Test that update request with provider api key updates the provider api key."""
        mock_validate.return_value = (True, ['gemini-1.5-pro', 'gemini-1.5-flash'])
        
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, name="Test Provider")
        original_api_key = provider.provider_api_key
        new_api_key = 'new-api-key-12345'

        detail_url = f'/api/ai-providers/{provider.uuid}/'
        update_data = {'name': 'Updated Name', 'provider_api_key': new_api_key}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        provider.refresh_from_db()
        self.assertEqual(provider.name, 'Updated Name')
        self.assertEqual(provider.provider_api_key, new_api_key)
        self.assertNotEqual(provider.provider_api_key, original_api_key)

    def test_update_with_empty_api_key_does_not_change_api_key(self):
        """Test that update request with empty string provider api key does not update the provider api key."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, name="Test Provider")
        original_api_key = provider.provider_api_key

        detail_url = f'/api/ai-providers/{provider.uuid}/'
        update_data = {'name': 'Updated Name', 'provider_api_key': ''}
        with patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider') as mock_validate:
            mock_validate.return_value = (True, ['gpt-3.5-turbo'])
            response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        provider.refresh_from_db()
        self.assertEqual(provider.name, 'Updated Name')
        self.assertEqual(provider.provider_api_key, original_api_key)

    def test_update_with_whitespace_api_key_does_not_change_api_key(self):
        """Test that update request with whitespace-only provider api key does not update the provider api key."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        provider = AIProviderFactory(creator=user, name="Test Provider")
        original_api_key = provider.provider_api_key

        detail_url = f'/api/ai-providers/{provider.uuid}/'
        update_data = {'name': 'Updated Name', 'provider_api_key': '   '}
        with patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider') as mock_validate:
            mock_validate.return_value = (True, ['gpt-3.5-turbo'])
            response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        provider.refresh_from_db()
        self.assertEqual(provider.name, 'Updated Name')
        self.assertEqual(provider.provider_api_key, original_api_key)

    @patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider')
    def test_api_key_is_encrypted_in_database(self, mock_validate):
        """Test that provider_api_key is encrypted when stored in the database."""
        mock_validate.return_value = (True, ['gemini-1.5-pro', 'gemini-1.5-flash'])
        
        user = UserFactory()
        self.client.force_authenticate(user=user)

        api_key = 'test-api-key-12345'
        create_data = {
            'name': 'Test Provider',
            'provider': 'gemini',
            'base_url': 'https://generativelanguage.googleapis.com',
            'provider_api_key': api_key
        }

        response = self.client.post(self.list_url, create_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        provider = AIProvider.objects.get(uuid=response.json()['ai_provider']['uuid'])

        self.assertEqual(provider.provider_api_key, api_key)

        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT provider_api_key FROM core_aiprovider WHERE id = %s", [provider.id])
            raw_db_value = cursor.fetchone()[0]
            self.assertNotEqual(raw_db_value, api_key)
            self.assertTrue(raw_db_value.startswith('gAAAAA'))


    @patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider')
    def test_create_with_supported_provider_gemini(self, mock_validate):
        """Test that AI provider can be created with supported 'gemini' provider."""
        mock_validate.return_value = (True, ['gemini-1.5-pro', 'gemini-1.5-flash'])
        
        user = UserFactory()
        data = {
            'name': 'My Google Gemini Provider',
            'provider': 'gemini',
            'base_url': 'https://generativelanguage.googleapis.com',
            'provider_api_key': 'test-api-key-12345'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})

        assert serializer.is_valid(), f"Serializer should be valid but got errors: {serializer.errors}"
        provider = serializer.save()

        assert provider.name == 'My Google Gemini Provider'
        assert provider.provider == 'gemini'
        assert provider.metadata['base_url'] == 'https://generativelanguage.googleapis.com'
        assert provider.creator == user

    @patch('core.services.factories.ai_provider_factory.AIProviderFactory.validate_provider')
    def test_create_with_supported_provider_custom(self, mock_validate):
        """Test that AI provider can be created with supported 'custom' provider."""
        mock_validate.return_value = (True, ['custom-model-1', 'custom-model-2'])
        
        user = UserFactory()
        data = {
            'name': 'My Custom Provider',
            'provider': 'custom',
            'base_url': 'https://my-custom-api.com',
            'provider_api_key': 'test-api-key-67890'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})

        assert serializer.is_valid()
        provider = serializer.save()

        assert provider.name == 'My Custom Provider'
        assert provider.provider == 'custom'
        assert provider.metadata['base_url'] == 'https://my-custom-api.com'
        assert provider.creator == user

    def test_create_with_unsupported_provider_fails(self):
        """Test that AI provider creation fails with unsupported provider."""
        user = UserFactory()
        data = {
            'name': 'My Unsupported Provider',
            'provider': 'unsupported_provider',
            'base_url': 'https://unsupported-api.com',
            'provider_api_key': 'test-api-key-12345'
        }

        serializer = AIProviderCreateSerializer(data=data, context={'request': type('MockRequest', (), {'user': user})()})

        assert not serializer.is_valid()
        assert 'provider' in serializer.errors
        assert "not supported" in str(serializer.errors['provider'][0])
        assert "Google Gemini" in str(serializer.errors['provider'][0])
