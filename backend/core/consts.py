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

SUPPORTED_NOTIFICATION_PROVIDERS = [
    {
        'id': 'email',
        'label': 'Email',
        'description': 'Email notifications via SMTP',
        'config_fields': ['email'],
        'required_fields': ['email']
    },
    {
        'id': 'slack',
        'label': 'Slack',
        'description': 'Slack webhook notifications',
        'config_fields': ['webhookUrl'],
        'required_fields': ['webhookUrl']
    },
    {
        'id': 'discord',
        'label': 'Discord',
        'description': 'Discord webhook notifications',
        'config_fields': ['webhookUrl'],
        'required_fields': ['webhookUrl']
    }
]
