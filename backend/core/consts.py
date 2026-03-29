DASHBOARD_USER_ID_PREFIX = "dashboard"
LIVE_UPDATES_PREFIX = "live"

AI_ROLE_AI_AGENT="assistant"
AI_ROLE_HUMAN_AGENT="assistant"
AI_ROLE_USER="user"
AI_ROLE_SYSTEM="system"
AI_ROLE_UNKNOWN="unknown"

SUPPORTED_AI_PROVIDERS = [
    {
        'id': 'gemini',
        'label': 'Google Gemini',
        'base_url': 'https://generativelanguage.googleapis.com/v1beta'
    },
    {
        'id': 'custom',
        'label': 'Custom Provider',
        'base_url': ''
    }
]

SUPPORTED_INTEGRATIONS = [
    {
        'id': 'github',
        'label': 'GitHub',
        'description': 'Connect your GitHub account for repository ingestion and issue management.',
        'supported_types': ['version_control', 'project_management'],
        'credential_fields': ['token'],
        'validate': 'core.integrations.github_validator.validate_github_token',
    }
]
