import os
import django
from django.conf import settings
from pathlib import Path

if not settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.test_settings')

    base_dir = Path(__file__).resolve().parent.parent.parent
    env_path = base_dir / '.env'
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)

    django.setup()

import pytest
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from factory.django import DjangoModelFactory
import factory

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client, user


class BaseTestCase(TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()


class BaseAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def tearDown(self):
        super().tearDown()


class BaseServiceTestCase(TestCase):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()


class BaseFactory(DjangoModelFactory):
    class Meta:
        abstract = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return super()._create(model_class, *args, **kwargs)
