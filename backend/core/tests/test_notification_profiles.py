import pytest
from rest_framework import status

from core.models import NotificationProfile, AppNotificationProfile
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import UserFactory, ApplicationFactory, NotificationProfileFactory


@pytest.mark.api
class TestNotificationProfileAPI(BaseAPITestCase):
    """Tests for /api/notification-profiles/ endpoints."""

    def setUp(self):
        super().setUp()
        self.url = '/api/notification-profiles/'

    # ------------------------------------------------------------------ auth
    def test_unauthenticated_returns_403(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ------------------------------------------------------------------ list
    def test_list_returns_only_own_profiles(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        NotificationProfileFactory(owner=user, name='Mine')
        NotificationProfileFactory(owner=UserFactory(), name='Not Mine')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [p['name'] for p in response.json()['results']]
        self.assertIn('Mine', names)
        self.assertNotIn('Not Mine', names)

    def test_list_includes_supported_providers(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('supported_providers', response.json())

    # ----------------------------------------------------------------- create
    def test_create_slack_profile(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'name': 'Slack Alerts',
            'type': 'slack',
            'config': {'webhookUrl': 'https://hooks.slack.com/services/abc/def/ghi'},
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertEqual(body['name'], 'Slack Alerts')
        self.assertEqual(body['type'], 'slack')
        # config is write-only — must not appear in response
        self.assertNotIn('config', body)
        # config_meta should indicate webhook is set
        self.assertTrue(body['config_meta']['hasWebhookUrl'])

    def test_create_discord_profile(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'name': 'Discord Alerts',
            'type': 'discord',
            'config': {'webhookUrl': 'https://discord.com/api/webhooks/123/abc'},
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()['config_meta']['hasWebhookUrl'])

    def test_create_email_profile(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'name': 'Email Alerts',
            'type': 'email',
            'config': {'email': 'alerts@example.com'},
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()['config_meta']['hasEmail'])

    def test_create_sets_owner_to_requesting_user(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'name': 'My Profile',
            'type': 'slack',
            'config': {'webhookUrl': 'https://hooks.slack.com/services/x/y/z'},
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['owner'], user.id)

    # --------------------------------------------------- create validation
    def test_create_slack_with_wrong_domain_fails(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'name': 'Bad Slack',
            'type': 'slack',
            'config': {'webhookUrl': 'https://discord.com/api/webhooks/bad'},
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_discord_with_wrong_domain_fails(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'name': 'Bad Discord',
            'type': 'discord',
            'config': {'webhookUrl': 'https://hooks.slack.com/services/bad'},
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_email_with_invalid_format_fails(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'name': 'Bad Email',
            'type': 'email',
            'config': {'email': 'not-an-email'},
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_missing_webhook_url_fails(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {'name': 'No Webhook', 'type': 'slack', 'config': {}}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------------------------- config never exposed in response
    def test_raw_config_values_not_in_response(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        data = {
            'name': 'Secret Profile',
            'type': 'slack',
            'config': {'webhookUrl': 'https://hooks.slack.com/services/secret'},
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.json()
        self.assertNotIn('config', body)
        self.assertNotIn('secret', str(body))

    # ----------------------------------------------------------------- update
    def test_patch_own_profile_name(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        profile = NotificationProfileFactory(owner=user, name='Old Name')

        response = self.client.patch(
            f'{self.url}{profile.uuid}/',
            {'name': 'New Name'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], 'New Name')
        profile.refresh_from_db()
        self.assertEqual(profile.name, 'New Name')

    def test_patch_updates_webhook_url(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        profile = NotificationProfileFactory(owner=user, type='slack')

        new_url = 'https://hooks.slack.com/services/new/url/here'
        response = self.client.patch(
            f'{self.url}{profile.uuid}/',
            {'config': {'webhookUrl': new_url}},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.config['webhookUrl'], new_url)

    def test_patch_other_users_profile_returns_404(self):
        user_a = UserFactory()
        user_b = UserFactory()
        self.client.force_authenticate(user=user_a)
        profile = NotificationProfileFactory(owner=user_b)

        response = self.client.patch(
            f'{self.url}{profile.uuid}/',
            {'name': 'Hacked'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ----------------------------------------------------------------- delete
    def test_delete_own_profile(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        profile = NotificationProfileFactory(owner=user)

        response = self.client.delete(f'{self.url}{profile.uuid}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['detail'], 'deleted')
        self.assertFalse(NotificationProfile.objects.filter(uuid=profile.uuid).exists())

    def test_delete_other_users_profile_returns_404(self):
        user_a = UserFactory()
        user_b = UserFactory()
        self.client.force_authenticate(user=user_a)
        profile = NotificationProfileFactory(owner=user_b)

        response = self.client.delete(f'{self.url}{profile.uuid}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(NotificationProfile.objects.filter(uuid=profile.uuid).exists())

    # ----------------------------------------------------------------- toggle
    def test_toggle_disables_enabled_profile(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        profile = NotificationProfileFactory(owner=user, is_enabled=True)

        response = self.client.post(f'{self.url}{profile.uuid}/toggle/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertFalse(profile.is_enabled)

    def test_toggle_enables_disabled_profile(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        profile = NotificationProfileFactory(owner=user, is_enabled=False)

        response = self.client.post(f'{self.url}{profile.uuid}/toggle/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertTrue(profile.is_enabled)

    # -------------------------------------------- config encrypted at rest
    def test_config_is_encrypted_in_database(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)

        webhook = 'https://hooks.slack.com/services/T/B/secret123'
        self.client.post(self.url, {
            'name': 'Enc Test',
            'type': 'slack',
            'config': {'webhookUrl': webhook},
        }, format='json')

        profile = NotificationProfile.objects.get(name='Enc Test', owner=user)

        # ORM decrypts transparently
        self.assertEqual(profile.config['webhookUrl'], webhook)

        # Raw DB value must be encrypted
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT config FROM core_notificationprofile WHERE id = %s',
                [profile.id],
            )
            raw = cursor.fetchone()[0]
        self.assertNotIn('secret123', raw)
        self.assertTrue(raw.startswith('gAAAAA'))


@pytest.mark.api
class TestAppNotificationUpdateAPI(BaseAPITestCase):
    """Tests for /api/applications/<uuid>/app-notification-update/"""

    def _url(self, app_uuid):
        return f'/api/applications/{app_uuid}/app-notification-update/'

    def test_link_profiles_to_app(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)
        p1 = NotificationProfileFactory(owner=user)
        p2 = NotificationProfileFactory(owner=user)

        response = self.client.patch(
            self._url(app.uuid),
            {'profile_uuids': [str(p1.uuid), str(p2.uuid)]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AppNotificationProfile.objects.filter(application=app).count(), 2)

    def test_link_replaces_existing(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)
        p1 = NotificationProfileFactory(owner=user)
        p2 = NotificationProfileFactory(owner=user)

        self.client.patch(self._url(app.uuid), {'profile_uuids': [str(p1.uuid)]}, format='json')
        self.client.patch(self._url(app.uuid), {'profile_uuids': [str(p2.uuid)]}, format='json')

        linked = AppNotificationProfile.objects.filter(application=app)
        self.assertEqual(linked.count(), 1)
        self.assertEqual(linked.first().notification_profile, p2)

    def test_cannot_link_other_users_profile(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)
        foreign_profile = NotificationProfileFactory(owner=UserFactory())

        response = self.client.patch(
            self._url(app.uuid),
            {'profile_uuids': [str(foreign_profile.uuid)]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Foreign profile silently ignored — nothing linked
        self.assertEqual(AppNotificationProfile.objects.filter(application=app).count(), 0)

    def test_cannot_update_other_users_app(self):
        user_a = UserFactory()
        user_b = UserFactory()
        self.client.force_authenticate(user=user_a)
        app_b = ApplicationFactory(owner=user_b)
        profile = NotificationProfileFactory(owner=user_a)

        response = self.client.patch(
            self._url(app_b.uuid),
            {'profile_uuids': [str(profile.uuid)]},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_payload_returns_400(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)

        response = self.client.patch(
            self._url(app.uuid),
            {'profile_uuids': 'not-a-list'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_list_unlinks_all(self):
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)
        profile = NotificationProfileFactory(owner=user)

        self.client.patch(self._url(app.uuid), {'profile_uuids': [str(profile.uuid)]}, format='json')
        self.client.patch(self._url(app.uuid), {'profile_uuids': []}, format='json')

        self.assertEqual(AppNotificationProfile.objects.filter(application=app).count(), 0)

    def test_unauthenticated_returns_403(self):
        app = ApplicationFactory()
        response = self.client.patch(self._url(app.uuid), {'profile_uuids': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
