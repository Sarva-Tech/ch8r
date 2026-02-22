---
description: Code standards and conventions for Ch8r project
trigger: always_on
---

# Ch8r Project Development Rules

## General Architecture Rules

- **Monorepo Structure**: This project follows a monorepo structure with backend (Django), frontend (Nuxt.js), and widget components
- **API First Design**: All features must be designed with API-first approach. Backend APIs should be fully functional before frontend implementation
- **Separation of Concerns**: Maintain clear separation between backend, frontend, and widget codebases

## Backend (Django) Rules

### Code Structure

- Follow Django best practices and conventions
- Use Django REST Framework for all API endpoints
- Implement proper serializer validation using Pydantic models
- All business logic should be in services layer, not in views or models
- Refactor code to utilities when needed

### Database & Models

- All models must have proper field validation and constraints
- Use Django migrations for all schema changes
- Implement proper indexing for frequently queried fields
- Use Django's built-in authentication and authorization

### API Standards

- Use RESTful API design principles
- Implement proper HTTP status codes
- All API responses must be consistent format
- Use API key authentication for external access
<!-- - Implement rate limiting for public endpoints -->

### Security Requirements

- Never commit API keys, passwords, or secrets to git
- Use environment variables for all sensitive configuration
- Implement proper input validation and sanitization
- Use Django's built-in CSRF protection
- Validate all file uploads (type, size, content)

### AI/ML Integration

- All AI model interactions must be abstracted through service classes
- Implement proper error handling for AI API failures
- Log all AI interactions for debugging and monitoring

## Frontend (Nuxt.js) Rules

### Code Structure

- Follow Vue.js composition API patterns
- Use TypeScript for all new components
- Implement proper component hierarchy and reusability
- Use Pinia for state management

### UI/UX Standards

- Follow established design system using ShadCN Vue components
- Use Tailwind CSS for styling - no custom CSS unless absolutely necessary
- Implement responsive design for all components
- Use proper loading states and error handling

### Performance Requirements

- Implement lazy loading for heavy components
- Optimize bundle size with dynamic imports
- Use Nuxt's built-in optimization features
- Implement proper caching strategies

### API Integration

- Use composables for API calls
- Implement proper error handling and user feedback
- Use TypeScript interfaces for all API responses
- Implement retry logic for failed requests

## Widget Development Rules

### Embeddable Standards

- Widget must be self-contained with no external dependencies
- Use vanilla JavaScript or minimal framework footprint
- Implement proper sandboxing and isolation
- Support multiple embedding methods (iframe, script tag)

### Communication Protocols

- Use postMessage API for cross-origin communication
- Implement proper message validation and sanitization
- Handle all edge cases for parent window interactions

<!-- ## Testing Requirements

### Backend Testing

- Write unit tests for all business logic
- Test API endpoints with proper request/response validation
- Use Django's test framework and factory patterns
- Achieve minimum 80% code coverage

### Frontend Testing

- Write unit tests for components and composables
- Implement E2E tests for critical user flows
- Test API integration with mock responses
- Use Vue Test Utils and Playwright -->

<!-- ## Development Workflow

### Git Workflow

- Use feature branches for all development
- Write descriptive commit messages following conventional commits
- Create pull requests for all changes
- Require code review before merging -->

### Environment Setup

- Use Docker for Qdrant vector database
- Maintain separate .env files for each environment
- Use virtual environments for Python dependencies
- Use Node.js 22.x as specified in package.json

### Code Quality

- Use ESLint and Prettier for frontend code formatting
- Use Black and isort for Python code formatting
- Run pre-commit hooks before committing
- Fix all linting errors before merging

## Security & Compliance

### Data Protection

- Implement proper data encryption at rest and in transit
- Follow GDPR guidelines for user data handling
- Implement proper audit logging
- Regular security scans and dependency updates

### AI Ethics

- Ensure AI responses are unbiased and fair
- Implement proper content filtering
- Monitor AI model performance and accuracy
- Provide human escalation paths when needed

## Documentation Standards

<!-- ### API Documentation

- Use OpenAPI/Swagger for all API documentation
- Include examples for all endpoints
- Document error responses and status codes
- Keep documentation in sync with code changes -->

### Code Documentation

- Write clear docstrings for all functions and classes
- Use type hints for Python code
  <!-- - Document complex business logic -->
  <!-- - Maintain README files for each major component -->

## Performance Monitoring

### Backend Metrics

<!-- - Monitor API response times and error rates
- Track database query performance -->

- Monitor Celery task execution
- Set up alerts for critical failures

### Frontend Metrics

<!-- - Monitor Core Web Vitals -->
<!-- - Track bundle size and loading times -->

- Monitor user interaction performance
- Implement error tracking and reporting
