---
description: Workflow rules and development processes for Ch8r project
trigger: manual
---

# Development Workflow Rules

## Git Workflow

### Branch Strategy

- Use GitFlow branching model
- `main` branch for production releases
- `develop` branch for integration
- `feature/*` branches for new features
- `hotfix/*` branches for urgent fixes
- `release/*` branches for release preparation

### Commit Standards

- Follow conventional commit format
- Use descriptive commit messages
- Include issue tracking numbers
- Keep commits focused and atomic

```
feat: add user authentication system
fix: resolve API timeout issue
docs: update API documentation
test: add unit tests for user service
refactor: optimize database queries
```

### Pull Request Process

- Create PRs for all changes
- Require code review approval
- Include automated tests
- Update documentation as needed

## Development Environment Setup

### Backend Environment

```bash
# Backend setup commands
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Configure .env file
python manage.py migrate
python manage.py runserver
```

### Frontend Environment

```bash
# Frontend setup commands
cd frontend
npm install
cp .env.example .env
# Configure .env file
npm run dev
```

### Database Setup

```bash
# Start Qdrant vector database
docker run -p 6333:6333 -p 6334:6334 \
  -v ~/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

# Start Celery worker
cd backend
celery -A config worker -l info --pool=solo
```

## Code Quality Standards

### Backend Code Quality

- Use Black for code formatting
- Use isort for import sorting
- Use flake8 for linting
- Use mypy for type checking

```bash
# Backend quality checks
black .
isort .
flake8 .
mypy .
```

### Frontend Code Quality

- Use ESLint for code linting
- Use Prettier for code formatting
- Use TypeScript for type safety
- Use Vue.js specific linting rules

```bash
# Frontend quality checks
npm run lint
npm run format
npm run type-check
```

### Pre-commit Hooks

- Install pre-commit hooks
- Run quality checks before commits
- Prevent low-quality code commits
- Automate code formatting

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
```

## Testing Workflow

### Backend Testing

- Write tests before implementation (TDD)
- Use Django's test framework
- Test all business logic
- Achieve 80% code coverage

```bash
# Backend testing commands
python manage.py test
coverage run --source='.' manage.py test
coverage report
```

### Frontend Testing

- Test components with Vue Test Utils
- Use Playwright for E2E tests
- Test API integration
- Monitor test coverage

```bash
# Frontend testing commands
npm run test:unit
npm run test:e2e
npm run test:coverage
```

### Testing Strategy

- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for user flows
- Performance tests for critical paths

## Deployment Workflow

### Development Deployment

- Auto-deploy from `develop` branch
- Run automated tests
- Deploy to staging environment
- Notify team of deployment

### Production Deployment

- Manual deployment from `main` branch
- Full test suite execution
- Database migrations
- Post-deployment verification

### Deployment Checklist

- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Security scan passed
- [ ] Performance tests passed
- [ ] Rollback plan ready

## Code Review Process

### Review Guidelines

- Review code for functionality
- Check security implications
- Verify performance impact
- Ensure code quality standards

### Review Checklist

- [ ] Code follows project standards
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] Security is considered
- [ ] Performance is optimized

## Documentation Workflow

### API Documentation

- Use OpenAPI/Swagger for APIs
- Generate documentation automatically
- Include examples for all endpoints
- Keep documentation in sync

### Code Documentation

- Write clear docstrings
- Document complex algorithms
- Include usage examples
- Maintain README files

### Documentation Updates

- Update docs with code changes
- Review documentation regularly
- Use version control for docs
- Publish documentation for users

## Monitoring and Alerting

### Application Monitoring

- Monitor application performance
- Track error rates
- Monitor API response times
- Set up performance alerts

### Security Monitoring

- Monitor authentication failures
- Track suspicious activities
- Monitor data access patterns
- Set up security alerts

### Infrastructure Monitoring

- Monitor server resources
- Track database performance
- Monitor network connectivity
- Set up infrastructure alerts

## Incident Management

### Incident Response

- Define incident severity levels
- Create response procedures
- Establish communication channels
- Document incident resolution

### Post-Incident Review

- Analyze incident root cause
- Document lessons learned
- Implement preventive measures
- Update procedures as needed

## Release Management

### Release Planning

- Plan release features
- Estimate development effort
- Define release criteria
- Schedule release timeline

### Release Process

- Feature freeze before release
- Final testing phase
- Release candidate creation
- Production deployment

### Release Communication

- Announce upcoming releases
- Document release notes
- Communicate changes to users
- Provide migration guides

## Team Collaboration

### Communication Standards

- Use appropriate communication channels
- Document important decisions
- Regular team meetings
- Clear assignment of responsibilities

### Knowledge Sharing

- Regular tech talks
- Code review discussions
- Documentation sharing
- Mentorship programs

## Continuous Improvement

### Process Improvement

- Regular process reviews
- Gather team feedback
- Implement improvements
- Measure process effectiveness

### Tool Improvement

- Evaluate new tools regularly
- Automate repetitive tasks
- Improve development workflows
- Optimize tool configurations
