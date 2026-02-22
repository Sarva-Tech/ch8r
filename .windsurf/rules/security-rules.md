---
description: Security and compliance rules for Ch8r project
trigger: manual
---

# Security & Compliance Rules

## General Security Principles

### Zero Trust Architecture

- Never trust user input - validate everything
- Implement principle of least privilege
- Use defense in depth approach
- Regular security audits and penetration testing

### Data Protection

- Encrypt sensitive data at rest and in transit
- Implement proper data retention policies
- Follow GDPR and data protection regulations
- Secure backup and recovery procedures

## Backend Security

### Authentication & Authorization

- Use Django's built-in authentication system
- Implement multi-factor authentication for admin access
- Use JWT tokens for API authentication
- Implement proper session management

```python
# Example secure authentication
class SecureAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Validate session/token
        # Check user permissions
        # Log authentication attempts
        return self.get_response(request)
```

### API Security

- Use API keys for external access
- Implement rate limiting
- Use HTTPS for all API endpoints
- Validate all API requests

```python
# Example API security
class APIKeyPermission(BasePermission):
    def has_permission(self, request, view):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return False

        # Validate API key
        return APIKey.objects.filter(key=api_key, is_active=True).exists()
```

### Database Security

- Use parameterized queries to prevent SQL injection
- Implement proper database user permissions
- Encrypt sensitive database fields
- Regular database security updates

### File Upload Security

- Validate file types and sizes
- Scan uploaded files for malware
- Store files in secure locations
- Implement proper access controls

```python
# Example secure file upload
class SecureFileUpload:
    ALLOWED_TYPES = ['pdf', 'docx', 'txt']
    MAX_SIZE = 10 * 1024 * 1024  # 10MB

    def validate_file(self, file):
        # Check file type
        # Check file size
        # Scan for malware
        pass
```

## Frontend Security

### Client-Side Security

- Implement Content Security Policy (CSP)
- Sanitize user inputs to prevent XSS
- Use secure cookie practices
- Implement proper authentication state management

```typescript
// Example secure input handling
export const sanitizeInput = (input: string): string => {
  return DOMPurify.sanitize(input, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong'],
    ALLOWED_ATTR: [],
  })
}
```

### API Communication Security

- Use HTTPS for all API calls
- Implement proper token storage
- Use secure headers for API requests
- Handle authentication failures gracefully

```typescript
// Example secure API client
export const secureApiClient = {
  request: async (endpoint: string, options: RequestInit = {}) => {
    const token = getSecureToken()
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    }

    return await $fetch(endpoint, {
      ...options,
      headers,
      credentials: 'include',
    })
  },
}
```

### Data Storage Security

- Use httpOnly cookies for sensitive data
- Implement proper localStorage security
- Encrypt sensitive client-side data
- Clear sensitive data on logout

## AI/ML Security

### AI Model Security

- Validate all AI model inputs
- Sanitize AI model outputs
- Implement prompt injection protection
- Monitor AI model behavior

```python
# Example secure AI interaction
class SecureAIService:
    def __init__(self):
        self.input_validator = InputValidator()
        self.output_sanitizer = OutputSanitizer()

    def generate_response(self, prompt: str) -> str:
        # Validate input
        validated_prompt = self.input_validator.validate(prompt)

        # Generate response
        response = self.ai_model.generate(validated_prompt)

        # Sanitize output
        sanitized_response = self.output_sanitizer.sanitize(response)

        return sanitized_response
```

### Data Privacy in AI

- Anonymize user data before AI processing
- Implement proper data retention for AI interactions
- Use privacy-preserving AI techniques
- Monitor AI model for bias and fairness

## Widget Security

### Cross-Origin Security

- Use postMessage API securely
- Validate all cross-origin messages
- Implement proper sandboxing
- Use secure communication protocols

```javascript
// Example secure cross-origin communication
class SecureWidgetCommunication {
  constructor() {
    this.allowedOrigins = ['https://trusted-domain.com']
    this.messageHandlers = new Map()
  }

  init() {
    window.addEventListener('message', (event) => {
      if (!this.allowedOrigins.includes(event.origin)) {
        return
      }

      this.handleMessage(event.data)
    })
  }

  handleMessage(data) {
    // Validate message structure
    // Process message
    // Send response
  }
}
```

### Embed Security

- Implement proper iframe security
- Use CSP headers for embedded content
- Validate widget configuration
- Prevent clickjacking attacks

## Compliance Requirements

### GDPR Compliance

- Implement proper consent management
- Provide data export functionality
- Implement data deletion procedures
- Maintain privacy policies

### Data Retention

- Implement automatic data deletion
- Archive old data appropriately
- Comply with legal requirements
- Document retention policies

### Audit Requirements

- Log all security-relevant events
- Implement audit trails
- Regular security assessments
- Compliance reporting

## Security Monitoring

### Logging and Alerting

- Log all security events
- Implement real-time alerts
- Monitor for suspicious activity
- Regular security reviews

```python
# Example security logging
import logging

security_logger = logging.getLogger('security')

def log_security_event(event_type: str, details: dict):
    security_logger.info(f"Security Event: {event_type}", extra=details)

    # Send alert if critical
    if event_type in ['authentication_failure', 'suspicious_activity']:
        send_security_alert(event_type, details)
```

### Incident Response

- Implement incident response procedures
- Have emergency contact procedures
- Regular security drills
- Document security incidents

## Development Security

### Secure Development Practices

- Regular security training for developers
- Secure code review processes
- Use security testing tools
- Regular dependency updates

### Dependency Security

- Regularly scan for vulnerabilities
- Use dependency checking tools
- Update vulnerable packages promptly
- Monitor security advisories

```bash
# Example security scanning commands
pip-audit  # Python dependency security scanner
npm audit  # Node.js dependency security scanner
bandit -r .  # Python code security scanner
```

### Environment Security

- Secure development environments
- Use environment-specific configurations
- Implement proper secrets management
- Regular environment security audits

## Testing Security

### Security Testing

- Regular penetration testing
- Vulnerability scanning
- Security unit tests
- Integration security tests

```python
# Example security test
class SecurityTestCase(TestCase):
    def test_sql_injection_protection(self):
        malicious_input = "'; DROP TABLE users; --"
        response = self.client.post('/api/endpoint/', {
            'input': malicious_input
        })

        # Verify no SQL injection occurred
        self.assertEqual(response.status_code, 400)
        self.assertTrue(User.objects.exists())
```

### Code Security Review

- Regular security code reviews
- Static analysis security testing
- Manual security assessments
- Third-party security audits
