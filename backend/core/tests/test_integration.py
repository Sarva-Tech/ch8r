import pytest
from django.db import IntegrityError
from rest_framework import status
from unittest.mock import patch

from core.models import Integration, AppIntegration
from core.models.base_model import BaseModel
from core.tests.conftest import BaseAPITestCase
from core.tests.factories import (
    UserFactory,
    ApplicationFactory,
    IntegrationFactory,
    AppIntegrationFactory,
)

MOCK_TARGET = 'core.integrations.github_validator.validate_github_token'


@pytest.mark.api
class TestIntegrationAPI(BaseAPITestCase):
    """Test suite for Integration API endpoints."""

    def setUp(self):
        super().setUp()
        self.list_url = '/api/integrations/'

    def test_list_integrations_authenticated(self):
        """User sees only their own integrations; response includes supported_integrations list."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        IntegrationFactory(creator=user, name='My Integration')
        other_user = UserFactory()
        IntegrationFactory(creator=other_user, name='Other Integration')

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['name'], 'My Integration')
        self.assertIn('supported_integrations', data)
        self.assertIsInstance(data['supported_integrations'], list)

    def test_list_integrations_unauthenticated(self):
        """Unauthenticated requests return 403."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(MOCK_TARGET, return_value=(True, '', {}))
    def test_create_integration_valid_token(self, mock_validate):
        """Valid token: POST returns 201."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.list_url, {
            'name': 'My GitHub',
            'provider': 'github',
            'token': 'ghp_validtoken',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['name'], 'My GitHub')

    @patch(MOCK_TARGET, return_value=(False, 'bad token', {}))
    def test_create_integration_invalid_token(self, mock_validate):
        """Invalid token: POST returns 400 with error key."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.list_url, {
            'name': 'Bad GitHub',
            'provider': 'github',
            'token': 'ghp_badtoken',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())

    def test_create_integration_unsupported_provider(self):
        """POST with unsupported provider returns 400."""
        user = UserFactory()
        self.client.force_authenticate(user=user)

        response = self.client.post(self.list_url, {
            'name': 'Unknown',
            'provider': 'unsupported',
            'token': 'sometoken',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch(MOCK_TARGET, return_value=(True, '', {}))
    def test_retrieve_own_integration(self, mock_validate):
        """GET detail of own integration returns 200."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        integration = IntegrationFactory(creator=user)

        response = self.client.get(f'{self.list_url}{integration.uuid}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(MOCK_TARGET, return_value=(True, '', {}))
    def test_retrieve_other_users_integration(self, mock_validate):
        """GET detail of another user's integration returns 404."""
        user_a = UserFactory()
        user_b = UserFactory()
        integration = IntegrationFactory(creator=user_b)

        self.client.force_authenticate(user=user_a)
        response = self.client.get(f'{self.list_url}{integration.uuid}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch(MOCK_TARGET, return_value=(True, '', {}))
    def test_update_own_integration(self, mock_validate):
        """PATCH name of own integration returns 200."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        integration = IntegrationFactory(creator=user, name='Old Name')

        response = self.client.patch(
            f'{self.list_url}{integration.uuid}/',
            {'name': 'New Name'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], 'New Name')

    def test_update_other_users_integration(self):
        """PATCH another user's integration returns 404."""
        user_a = UserFactory()
        user_b = UserFactory()
        integration = IntegrationFactory(creator=user_b)

        self.client.force_authenticate(user=user_a)
        response = self.client.patch(
            f'{self.list_url}{integration.uuid}/',
            {'name': 'Hacked'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_integration(self):
        """DELETE own integration returns 200 with {"detail": "deleted"}."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        integration = IntegrationFactory(creator=user)

        response = self.client.delete(f'{self.list_url}{integration.uuid}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'detail': 'deleted'})

    def test_delete_other_users_integration(self):
        """DELETE another user's integration returns 404."""
        user_a = UserFactory()
        user_b = UserFactory()
        integration = IntegrationFactory(creator=user_b)

        self.client.force_authenticate(user=user_a)
        response = self.client.delete(f'{self.list_url}{integration.uuid}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_integration_model_has_no_type_field(self):
        """Integration model has no 'type' attribute in _meta.fields."""
        field_names = [f.name for f in Integration._meta.fields]
        self.assertNotIn('type', field_names)

    def test_integration_uses_base_model(self):
        """Integration inherits from BaseModel."""
        self.assertTrue(issubclass(Integration, BaseModel))

@pytest.mark.api
class TestAppIntegrationAPI(BaseAPITestCase):
    """Test suite for AppIntegration API endpoints."""

    def _app_integrations_url(self, app_uuid):
        return f'/api/applications/{app_uuid}/integrations/'

    def _app_integration_detail_url(self, app_uuid, integration_uuid):
        return f'/api/applications/{app_uuid}/integrations/{integration_uuid}/'

    @patch(MOCK_TARGET, return_value=(True, '', {}))
    def test_create_app_integration_valid(self, mock_validate):
        """Mock validator, create integration, POST to app integrations returns 201."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)

        response = self.client.post(
            self._app_integrations_url(app.uuid),
            {
                'integration_uuid': str(integration.uuid),
                'integration_type': 'version_control',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch(MOCK_TARGET, return_value=(True, '', {}))
    def test_create_app_integration_unsupported_type(self, mock_validate):
        """POST with unsupported integration_type returns 400."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)

        response = self.client.post(
            self._app_integrations_url(app.uuid),
            {
                'integration_uuid': str(integration.uuid),
                'integration_type': 'unsupported',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_app_integration_other_users_app(self):
        """POST to another user's app returns 404."""
        user_a = UserFactory()
        user_b = UserFactory()
        app = ApplicationFactory(owner=user_b)
        integration = IntegrationFactory(creator=user_a)

        self.client.force_authenticate(user=user_a)
        response = self.client.post(
            self._app_integrations_url(app.uuid),
            {
                'integration_uuid': str(integration.uuid),
                'integration_type': 'version_control',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_app_integration_other_users_integration(self):
        """Attaching another user's integration returns 400 with ownership error."""
        user_a = UserFactory()
        user_b = UserFactory()
        app = ApplicationFactory(owner=user_a)
        other_integration = IntegrationFactory(creator=user_b)

        self.client.force_authenticate(user=user_a)
        response = self.client.post(
            self._app_integrations_url(app.uuid),
            {
                'integration_uuid': str(other_integration.uuid),
                'integration_type': 'version_control',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You don't own this integration", str(response.json()))

    @patch(MOCK_TARGET, return_value=(True, '', {}))
    def test_app_integration_upsert(self, mock_validate):
        """POST twice with same integration_type results in DB count == 1."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)

        payload = {
            'integration_uuid': str(integration.uuid),
            'integration_type': 'version_control',
        }
        self.client.post(self._app_integrations_url(app.uuid), payload, format='json')
        self.client.post(self._app_integrations_url(app.uuid), payload, format='json')

        count = AppIntegration.objects.filter(
            application=app, integration_type='version_control'
        ).count()
        self.assertEqual(count, 1)

    def test_app_integration_unique_constraint(self):
        """Direct DB create of duplicate (application, integration_type) raises IntegrityError."""
        user = UserFactory()
        app = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)

        AppIntegration.objects.create(
            application=app,
            integration=integration,
            integration_type='version_control',
        )

        with self.assertRaises(IntegrityError):
            AppIntegration.objects.create(
                application=app,
                integration=integration,
                integration_type='version_control',
            )

    @patch(MOCK_TARGET, return_value=(True, '', {}))
    def test_delete_app_integration(self, mock_validate):
        """DELETE app integration returns 200 with {"detail": "deleted"}."""
        user = UserFactory()
        self.client.force_authenticate(user=user)
        app = ApplicationFactory(owner=user)
        integration = IntegrationFactory(creator=user)
        app_integration = AppIntegrationFactory(application=app, integration=integration)

        response = self.client.delete(
            self._app_integration_detail_url(app.uuid, app_integration.uuid)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {'detail': 'deleted'})
