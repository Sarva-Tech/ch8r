import pytest
from rest_framework import status

from core.models import AppNotificationProfile
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import (
    UserFactory,
    ApplicationFactory,
    NotificationProfileFactory
)


@pytest.mark.api
class TestAppNotificationProfileAPI(BaseAPITestCase):
    def setUp(self):
        super().setUp()

    def test_update_notifications_other_users_application(self):
        user_a = UserFactory()
        user_b = UserFactory()

        app_b = ApplicationFactory(owner=user_b, name="User B's App")
        profile_a = NotificationProfileFactory(owner=user_a, name="User A's Profile", type="email")

        self.client.force_authenticate(user=user_a)

        url = f'/api/applications/{app_b.uuid}/notification-profiles/'
        data = {
            'profile_uuids': [str(profile_a.uuid)]
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        app_notification_profiles_count = AppNotificationProfile.objects.filter(application=app_b).count()
        self.assertEqual(app_notification_profiles_count, 0)
