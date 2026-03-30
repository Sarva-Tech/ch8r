import pytest
from rest_framework import status

from core.models import NotificationProfile
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import UserFactory, NotificationProfileFactory


@pytest.mark.api
class TestNotificationProfileAPI(BaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.list_url = '/api/notification-profiles/'

    def test_list_notification_profiles_authenticated_user(self):
        """Test that authenticated users can list their notification profiles."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile1 = NotificationProfileFactory(owner=user, name="Email Profile", type="email")
        profile2 = NotificationProfileFactory(owner=user, name="Slack Profile", type="slack")

        other_user = UserFactory()
        other_profile = NotificationProfileFactory(owner=other_user, name="Other User Profile", type="discord")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data['results']), 2)

        profile_names = [profile['name'] for profile in data['results']]
        self.assertIn("Email Profile", profile_names)
        self.assertIn("Slack Profile", profile_names)
        self.assertNotIn("Other User Profile", profile_names)

    def test_list_notification_profiles_unauthenticated(self):
        """Test that unauthenticated users cannot list notification profiles."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_own_notification_profile(self):
        """Test that user can retrieve their own notification profile."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(owner=user, name="My Email Profile", type="email")

        detail_url = f'/api/notification-profiles/{profile.id}/'
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "My Email Profile")
        self.assertEqual(response.data['type'], "email")

    def test_retrieve_other_users_notification_profile(self):
        """Test that user A cannot retrieve user B's notification profile."""
        user_a = UserFactory()
        user_b = UserFactory()

        profile_b = NotificationProfileFactory(owner=user_b, name="User B's Profile", type="email")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/notification-profiles/{profile_b.id}/'
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_notification_profile(self):
        """Test that authenticated user can create their own notification profile."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        create_data = {
            'name': 'My Slack Notifications',
            'type': 'slack',
            'config': {
                'webhookUrl': 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
            }
        }

        response = self.client.post(self.list_url, create_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['name'], 'My Slack Notifications')
        self.assertEqual(data['type'], 'slack')
        self.assertEqual(data['owner'], user.id)

        profile = NotificationProfile.objects.get(uuid=data['uuid'])
        self.assertEqual(profile.owner, user)
        self.assertEqual(profile.name, 'My Slack Notifications')

    def test_create_email_notification_profile(self):
        """Test that authenticated user can create an email notification profile."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        create_data = {
            'name': 'My Email Notifications',
            'type': 'email',
            'config': {
                'email': 'test@example.com'
            }
        }

        response = self.client.post(self.list_url, create_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        self.assertEqual(data['name'], 'My Email Notifications')
        self.assertEqual(data['type'], 'email')
        self.assertIn('email', data['config'])

    def test_update_own_notification_profile_name(self):
        """Test that authenticated user can update their own notification profile name."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(owner=user, name="Original Name", type="slack")

        detail_url = f'/api/notification-profiles/{profile.id}/'
        update_data = {'name': 'Updated Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['name'], 'Updated Name')
        self.assertEqual(data['owner'], user.id)

        profile.refresh_from_db()
        self.assertEqual(profile.name, 'Updated Name')

    def test_update_other_users_notification_profile(self):
        """Test that user A cannot update user B's notification profile."""
        user_a = UserFactory()
        user_b = UserFactory()

        profile_b = NotificationProfileFactory(owner=user_b, name="User B's Profile", type="email")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/notification-profiles/{profile_b.id}/'
        update_data = {'name': 'Hacked Name'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_notification_profile_webhook_url(self):
        """Test that update request with webhook URL updates the webhook URL."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(
            owner=user,
            name="Test Profile",
            type="slack",
            set_config={'webhookUrl': 'https://old-webhook.com'}
        )
        original_config = profile.config

        detail_url = f'/api/notification-profiles/{profile.id}/'
        new_webhook = 'https://hooks.slack.com/services/NEW/WEBHOOK/URL'
        update_data = {
            'name': 'Updated Name',
            'config': {'webhookUrl': new_webhook}
        }
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile.refresh_from_db()
        self.assertEqual(profile.name, 'Updated Name')
        self.assertEqual(profile.config['webhookUrl'], new_webhook)

    def test_update_notification_profile_email(self):
        """Test that update request with email updates the email."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(
            owner=user,
            name="Test Profile",
            type="email",
            set_config={'email': 'old@example.com'}
        )

        detail_url = f'/api/notification-profiles/{profile.id}/'
        new_email = 'new@example.com'
        update_data = {
            'name': 'Updated Name',
            'config': {'email': new_email}
        }
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile.refresh_from_db()
        self.assertEqual(profile.name, 'Updated Name')
        self.assertEqual(profile.config['email'], new_email)

    def test_update_without_config_does_not_change_config(self):
        """Test that update request without config does not change existing config."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(
            owner=user,
            name="Test Profile",
            type="slack",
            set_config={'webhookUrl': 'https://original-webhook.com'}
        )
        original_config = profile.config.copy()

        detail_url = f'/api/notification-profiles/{profile.id}/'
        update_data = {'name': 'Updated Name Only'}
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile.refresh_from_db()
        self.assertEqual(profile.name, 'Updated Name Only')
        self.assertEqual(profile.config, original_config)

    def test_update_with_empty_webhook_does_not_change_webhook(self):
        """Test that update request with empty webhook URL does not change the webhook URL."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(
            owner=user,
            name="Test Profile",
            type="slack",
            set_config={'webhookUrl': 'https://original-webhook.com'}
        )
        original_webhook = profile.config['webhookUrl']

        detail_url = f'/api/notification-profiles/{profile.id}/'
        update_data = {
            'name': 'Updated Name',
            'config': {'webhookUrl': ''}
        }
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile.refresh_from_db()
        self.assertEqual(profile.name, 'Updated Name')
        self.assertEqual(profile.config['webhookUrl'], original_webhook)

    def test_update_with_whitespace_webhook_does_not_change_webhook(self):
        """Test that update request with whitespace-only webhook URL does not change the webhook URL."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(
            owner=user,
            name="Test Profile",
            type="slack",
            set_config={'webhookUrl': 'https://original-webhook.com'}
        )
        original_webhook = profile.config['webhookUrl']

        detail_url = f'/api/notification-profiles/{profile.id}/'
        update_data = {
            'name': 'Updated Name',
            'config': {'webhookUrl': '   '}
        }
        response = self.client.patch(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile.refresh_from_db()
        self.assertEqual(profile.name, 'Updated Name')
        self.assertEqual(profile.config['webhookUrl'], original_webhook)

    def test_put_method_not_allowed(self):
        """Test that PUT method returns 405 Method Not Allowed."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(owner=user, name="Test Profile", type="email")

        detail_url = f'/api/notification-profiles/{profile.id}/'
        update_data = {
            'name': 'Updated Name',
            'type': 'slack',
            'config': {'webhookUrl': 'https://webhook.com'}
        }
        response = self.client.put(detail_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data['detail'], 'PUT method not allowed. Use PATCH instead.')

    def test_delete_own_notification_profile(self):
        """Test that authenticated user can delete their own notification profile."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        profile = NotificationProfileFactory(owner=user, name="Profile to Delete", type="email")

        detail_url = f'/api/notification-profiles/{profile.id}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(NotificationProfile.DoesNotExist):
            NotificationProfile.objects.get(id=profile.id)

    def test_delete_other_users_notification_profile(self):
        """Test that user A cannot delete user B's notification profile."""
        user_a = UserFactory()
        user_b = UserFactory()

        profile_b = NotificationProfileFactory(owner=user_b, name="User B's Profile", type="email")

        self.client.force_authenticate(user=user_a)

        detail_url = f'/api/notification-profiles/{profile_b.id}/'
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify profile still exists
        profile_exists = NotificationProfile.objects.filter(id=profile_b.id).exists()
        self.assertTrue(profile_exists)
