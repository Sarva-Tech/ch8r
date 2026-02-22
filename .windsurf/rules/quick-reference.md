---
description: Quick reference guide for Ch8r project development
trigger: always_on
---

# Ch8r Development Quick Reference

## Project Structure

```
ch8r/
├── backend/          # Django application
│   ├── config/      # Django settings
│   ├── core/        # Business logic
│   └── requirements.txt
├── frontend/         # Nuxt.js application
│   ├── components/  # Vue components
│   ├── pages/       # Page components
│   └── package.json
├── widget/          # Embeddable widget
└── .windsurf/       # Development rules
```

## Setup Commands

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Database Setup

```bash
docker run -p 6333:6333 -p 6334:6334 \
  -v ~/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant

cd backend
celery -A config worker -l info --pool=solo
```

## Code Standards

### Backend (Python/Django)

- Use Black for formatting: `black .`
- Use isort for imports: `isort .`
- Use flake8 for linting: `flake8 .`
- Follow Django best practices
- Write tests before implementation

### Frontend (Vue.js/Nuxt)

- Use ESLint: `npm run lint`
- Use Prettier: `npm run format`
- Use TypeScript for all new code
- Follow Vue.js Composition API
- Use ShadCN Vue components

## Git Workflow

### Commit Format

```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add tests
refactor: improve code
```

### Branch Strategy

- `main` - Production
- `develop` - Integration
- `feature/*` - New features
- `hotfix/*` - Urgent fixes

## Security Rules

### Never Commit

- API keys or passwords
- Environment files (.env)
- Database credentials
- Sensitive user data

### Always Validate

- User inputs
- API requests
- File uploads
- AI model inputs/outputs

## AI/ML Integration

### Services Structure

- Abstract AI service interface
- Multiple provider implementations
- Vector database with Qdrant
- Embedding caching

### Key Components

- Document processing
- Semantic search
- Context building
- Response generation

<!-- ## Testing Requirements

### Backend Testing

```bash
python manage.py test
coverage run --source='.' manage.py test
coverage report
```

### Frontend Testing

```bash
npm run test:unit
npm run test:e2e
npm run test:coverage
```

## Deployment Checklist

### Before Deploy

- [ ] All tests passing
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Security scan passed
- [ ] Performance tests passed

### Deploy Commands

```bash
# Backend
python manage.py migrate
python manage.py collectstatic --noinput

# Frontend
npm run build
npm run preview
``` -->

## Common Issues & Solutions

### Backend Issues

- **Migration conflicts**: Use `python manage.py migrate --fake`
- **Celery tasks not running**: Check Redis connection
- **AI API timeouts**: Implement retry logic

### Frontend Issues

- **Build failures**: Check Node.js version (use 22.x)
- **Component errors**: Check TypeScript interfaces
- **API errors**: Verify CORS settings

## Monitoring

### Key Metrics

- API response times
- Error rates
- Database query performance
- AI model costs

### Logging

- Use structured logging
- Include relevant context
- Monitor error logs
- Set up alerts

## Environment Variables

### Backend (.env)

```bash
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
OPENAI_API_KEY=your-openai-key
QDRANT_URL=http://localhost:6333
```

### Frontend (.env)

```bash
NUXT_PUBLIC_API_URL=http://localhost:8000
NUXT_PUBLIC_WIDGET_URL=http://localhost:3002
```

## Useful Commands

### Development

```bash
# Start all services
make dev  # or run individual services

# Code quality
black backend/
isort backend/
flake8 backend/
npm run lint  # frontend

# Testing
python manage.py test
npm run test:unit
```

### Database

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database
python manage.py flush
```

## Documentation

### API Documentation

- Available at `/api/docs/` (Swagger)
- Auto-generated from DRF serializers
- Include examples for all endpoints

### Code Documentation

- Use docstrings for all functions
- Include type hints
- Document complex algorithms
- Maintain README files

## Security Best Practices

### Authentication

- Use Django's built-in auth
- Implement JWT for APIs
- Use secure session management
- Enable CSRF protection

### Data Protection

- Encrypt sensitive data
- Use HTTPS everywhere
- Validate all inputs
- Implement proper logging

## Performance Optimization

### Backend

- Use database indexes
- Optimize queries with select_related/prefetch_related
- Implement caching strategies
- Monitor Celery task performance

### Frontend

- Use lazy loading
- Optimize bundle size
- Implement proper caching
- Monitor Core Web Vitals

## Troubleshooting

### Common Errors

- **Import errors**: Check Python path and virtual environment
- **Database errors**: Verify database connection and migrations
- **API errors**: Check CORS and authentication
- **Build errors**: Verify Node.js version and dependencies

### Debug Commands

```bash
# Django debug
python manage.py shell
python manage.py check

# Frontend debug
npm run build --analyze
npm run dev --debug
```

## Resources

### Documentation

- [Django Documentation](https://docs.djangoproject.com/)
- [Nuxt.js Documentation](https://nuxt.com/)
- [Vue.js Documentation](https://vuejs.org/)
- [Tailwind CSS](https://tailwindcss.com/)

### Tools

- [Black](https://black.readthedocs.io/) - Python formatter
- [ESLint](https://eslint.org/) - JavaScript linter
- [Prettier](https://prettier.io/) - Code formatter
- [Qdrant](https://qdrant.tech/) - Vector database
