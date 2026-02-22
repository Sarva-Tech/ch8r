---
description: Backend-specific development rules for Django application
trigger: always_on
---

# Backend Development Rules

## Django Architecture

### Project Structure

```
backend/
├── config/          # Django settings and URLs
├── core/           # Core business logic
│   ├── apps/       # Django apps
│   ├── services/   # Business logic services
│   ├── utils/      # Utility functions
│   └── models/     # Shared models
├── templates/      # Django templates
└── requirements.txt
```

### App Organization

- Each app should be self-contained with models, views, serializers, and URLs
- Use Django apps for logical grouping of functionality
- Keep apps loosely coupled with minimal dependencies

## Model Development

### Model Design Rules

- All models must inherit from `models.Model` with proper base classes
- Use descriptive field names following Python conventions
- Implement proper `__str__` methods for all models
- Add appropriate field constraints and validators

```python
class ExampleModel(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(3)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name
```

### Database Migration Rules

- Create migrations for all model changes
- Review migration files before applying
- Use data migrations for complex data transformations
- Test migrations on staging before production

## API Development

### View Class Structure

- Use Django REST Framework viewsets for standard CRUD operations
- Implement custom views for complex business logic
- Use proper permission classes for access control

```python
class ExampleViewSet(viewsets.ModelViewSet):
    queryset = ExampleModel.objects.all()
    serializer_class = ExampleSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        # Custom business logic
        pass
```

### Serializer Rules

- Use Pydantic models for complex validation
- Implement proper field validation
- Use nested serializers for related data
- Include read-only fields for computed values

```python
class ExampleSerializer(serializers.ModelSerializer):
    computed_field = serializers.ReadOnlyField()

    class Meta:
        model = ExampleModel
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate_name(self, value):
        # Custom validation logic
        return value
```

## Service Layer Architecture

### Service Class Design

- Implement business logic in service classes
- Keep views thin - delegate to services
- Use dependency injection for testability
- Handle all external API interactions in services

```python
class ExampleService:
    def __init__(self, repository=None):
        self.repository = repository or ExampleRepository()

    def process_data(self, data):
        # Business logic implementation
        pass

    def handle_ai_interaction(self, query):
        # AI service integration
        pass
```

### Error Handling

- Use custom exceptions for business logic errors
- Implement proper logging for debugging
- Return meaningful error messages to clients
- Handle external service failures gracefully

## Security Implementation

### Authentication & Authorization

- Use Django's built-in authentication system
- Implement role-based access control
- Use API keys for external access
- Validate all user inputs and permissions

### Data Validation

- Validate all incoming data using serializers
- Sanitize user inputs to prevent XSS
- Implement file upload validation
- Use Django's built-in CSRF protection

## AI/ML Integration Rules

### AI Service Abstraction

- Create abstract base classes for AI services
- Implement concrete classes for different AI providers
- Use factory pattern for AI service selection
- Cache AI responses to reduce costs

```python
class AIService(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

class OpenAIService(AIService):
    def generate_response(self, prompt: str) -> str:
        # OpenAI implementation
        pass
```

### Vector Database Integration

- Use Qdrant for vector storage and retrieval
- Implement proper embedding generation
- Use semantic search for knowledge base queries
- Monitor vector database performance

## Celery Task Management

### Task Design Rules

- Keep tasks idempotent and retry-safe
- Use proper task naming conventions
- Implement error handling and logging
- Set appropriate task timeouts

```python
@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id):
    try:
        # Document processing logic
        pass
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

### Task Monitoring

- Monitor task execution and failures
- Implement proper task routing
- Use task priorities for critical operations
- Set up alerts for task failures

<!-- ## Testing Requirements

### Unit Testing

- Test all business logic in services
- Mock external dependencies
- Test model validations and constraints
- Achieve minimum 80% code coverage

### API Testing

- Test all endpoints with various scenarios
- Test authentication and authorization
- Test error responses and status codes
- Use Django's test client for integration tests -->

## Performance Optimization

### Database Optimization

- Use select_related and prefetch_related for queries
- Implement proper database indexing
- Monitor query performance
- Use database connection pooling

<!-- ### Caching Strategy

- Cache frequently accessed data
- Use Redis for session storage
- Implement cache invalidation strategies
- Monitor cache hit rates -->

## Logging and Monitoring

### Logging Standards

- Use structured logging with loguru
- Include relevant context in log messages
- Implement different log levels appropriately
- Monitor application logs for errors

### Performance Monitoring

- Track API response times
- Monitor database query performance
- Set up alerts for critical metrics
- Use APM tools for application monitoring
