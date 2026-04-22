import factory
from faker import Faker as RealFaker
from django.contrib.auth.models import User
from core.models import (
    Application,
    AIProvider,
    Integration,
    AppIntegration,
    NotificationProfile,
    LLMModel,
    ChatRoom,
    KnowledgeBase,
    AppModel,
    AppNotificationProfile,
    ApplicationAPIKey,
    ApplicationWidgetToken
)

fake = RealFaker()

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
    provider = 'github'
    credentials = '{"token": "test_token_123"}'
    creator = factory.SubFactory(UserFactory)


class AppIntegrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AppIntegration

    application = factory.SubFactory(ApplicationFactory)
    integration = factory.SubFactory(IntegrationFactory)
    integration_type = 'version_control'
    metadata = factory.LazyFunction(lambda: {'repo': 'owner/repo'})
    is_active = True


class NotificationProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NotificationProfile

    name = factory.Sequence(lambda n: f"Notification Profile {n}")
    type = factory.Iterator(['email', 'slack', 'discord'])
    owner = factory.SubFactory(UserFactory)
    uuid = factory.Faker('uuid4')

    @factory.post_generation
    def set_config(obj, create, extracted, **kwargs):
        if obj.type == 'email':
            obj.config = extracted if extracted else {'email': fake.email()}
        else:
            obj.config = extracted if extracted else {'webhookUrl': f'https://hooks.{obj.type}.com/test/webhook'}


class LLMModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LLMModel

    name = factory.Sequence(lambda n: f"LLM Model {n}")
    api_key = factory.Faker('password')
    api_key_preview = factory.LazyAttribute(lambda obj: obj.api_key[:4] + '****')
    base_url = factory.Faker('url')
    model_name = factory.Iterator(['gpt-4', 'gpt-3.5-turbo', 'claude-3'])
    model_type = factory.Iterator(['text', 'embedding', 'image'])
    is_default = False
    owner = factory.SubFactory(UserFactory)


class ChatRoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChatRoom

    name = factory.Sequence(lambda n: f"Chat Room {n}")
    application = factory.SubFactory(ApplicationFactory)
    ai_provider = factory.SubFactory(AIProviderFactory)
    model = factory.Iterator(['gpt-4', 'gpt-3.5-turbo'])
    is_escalated = False


class KnowledgeBaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = KnowledgeBase

    application = factory.SubFactory(ApplicationFactory)
    source_type = factory.Iterator(['url', 'file', 'text', 'github'])
    path = factory.Faker('file_path')
    metadata = factory.LazyFunction(lambda: {'content': fake.text()})
    status = 'processed'


class AppModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AppModel

    application = factory.SubFactory(ApplicationFactory)
    llm_model = factory.SubFactory(LLMModelFactory)


class AppNotificationProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AppNotificationProfile

    application = factory.SubFactory(ApplicationFactory)
    notification_profile = factory.SubFactory(NotificationProfileFactory)


class ApplicationAPIKeyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApplicationAPIKey

    application = factory.SubFactory(ApplicationFactory)
    name = factory.Sequence(lambda n: f"API Key {n}")
    hashed_api_key = factory.Faker('password')
    permissions = factory.LazyFunction(lambda: ['read'])
    owner = factory.SubFactory(UserFactory)


class ApplicationWidgetTokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ApplicationWidgetToken

    application = factory.SubFactory(ApplicationFactory)
    label = factory.Sequence(lambda n: f"Widget Token {n}")
    rate_limit_count = 60
    rate_limit_period = 60
    is_active = True
