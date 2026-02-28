import factory
from django.contrib.auth.models import User
from core.models import (
    Application,
    AIProvider
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
    base_url = factory.Faker('url')
    is_builtin = False
    creator = factory.SubFactory(UserFactory)
