import factory
from django.contrib.auth.models import User
from core.models import (
    Application,
    AIProvider,
    Integration,
    AppIntegration
)

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'testuser{n}')
    email = factory.Sequence(lambda n: f'testuser{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

class ApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Application

    owner = factory.SubFactory(UserFactory)
    name = factory.Faker('company')
    uuid = factory.Faker('uuid4')

class AIProviderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AIProvider

    name = factory.Faker('company')
    provider = factory.Iterator(['openai', 'anthropic', 'google'])
    provider_api_key = factory.Faker('password')
    metadata = factory.LazyAttribute(lambda obj: {'base_url': 'https://example.com'})
    is_builtin = False
    creator = factory.SubFactory(UserFactory)


class IntegrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Integration

    name = factory.Sequence(lambda n: f"Integration {n}")
    integration_type = factory.Iterator(['github', 'slack', 'jira'])
    config = factory.LazyFunction(lambda: {
        'token': 'test_token',
        'api_url': 'https://api.example.com'
    })


class AppIntegrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AppIntegration

    application = factory.SubFactory(ApplicationFactory)
    integration = factory.SubFactory(IntegrationFactory)
    metadata = factory.LazyFunction(lambda: {
        'enabled': True,
        'sync_frequency': 'daily'
    })
