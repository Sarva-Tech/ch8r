import os
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatabaseConfig:
    """Database configuration"""
    name: str
    user: str
    password: str
    host: str
    port: int
    test_name: Optional[str] = None
    test_user: Optional[str] = None
    test_password: Optional[str] = None
    test_host: Optional[str] = None
    test_port: Optional[int] = None


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration"""
    local_host: str = "localhost"
    local_port: int = 6333
    cloud_host: Optional[str] = None
    cloud_port: Optional[int] = None
    cloud_api_key: Optional[str] = None
    connect_to_local: bool = False


@dataclass
class AIProviderConfig:
    """AI provider configuration"""
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration"""
    secret_key: str
    debug: bool = False
    allowed_hosts: list = None
    closed_alpha_signups: list = None
    require_account_approval: bool = False
    
    def __post_init__(self):
        if self.allowed_hosts is None:
            self.allowed_hosts = []
        if self.closed_alpha_signups is None:
            self.closed_alpha_signups = []


class ConfigManager:
    """
    Centralized configuration management with environment variable support
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent.parent.parent.parent
        self._env_loaded = False
    
    def _ensure_env_loaded(self):
        """Ensure environment variables are loaded"""
        if not self._env_loaded:
            try:
                from dotenv import load_dotenv
                load_dotenv(self.base_dir / '.env')
                self._env_loaded = True
            except ImportError:
                self._env_loaded = True
    
    def get_env_var(
        self, 
        key: str, 
        default: Any = None, 
        var_type: type = str
    ) -> Any:
        """
        Get environment variable with type conversion
        
        Args:
            key: Environment variable key
            default: Default value if not found
            var_type: Type to convert to
            
        Returns:
            Converted environment variable or default
        """
        self._ensure_env_loaded()
        
        value = os.environ.get(key)
        if value is None:
            return default
        
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif var_type == int:
            return int(value)
        elif var_type == float:
            return float(value)
        elif var_type == list:
            return [item.strip() for item in value.split(',') if item.strip()]
        else:
            return value
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return DatabaseConfig(
            name=self.get_env_var('DB_NAME', 'chatterbox'),
            user=self.get_env_var('DB_USER', 'postgres'),
            password=self.get_env_var('PASSWORD', 'postgres'),
            host=self.get_env_var('DB_HOST', 'localhost'),
            port=self.get_env_var('PORT', 5432, int),
            test_name=self.get_env_var('TEST_DB_NAME'),
            test_user=self.get_env_var('TEST_DB_USER'),
            test_password=self.get_env_var('TEST_DB_PASSWORD'),
            test_host=self.get_env_var('TEST_DB_HOST'),
            test_port=self.get_env_var('TEST_DB_PORT', None, int)
        )
    
    def get_qdrant_config(self) -> QdrantConfig:
        """Get Qdrant configuration"""
        return QdrantConfig(
            local_host=self.get_env_var('QDRANT_LOCAL_HOST', 'localhost'),
            local_port=self.get_env_var('QDRANT_LOCAL_PORT', 6333, int),
            cloud_host=self.get_env_var('QDRANT_CLOUD_HOST'),
            cloud_port=self.get_env_var('QDRANT_CLOUD_PORT', None, int),
            cloud_api_key=self.get_env_var('QDRANT_CLOUD_API_KEY'),
            connect_to_local=self.get_env_var('CONNECT_TO_LOCAL_VECTOR_DB', 'False', bool)
        )
    
    def get_ai_provider_config(self) -> AIProviderConfig:
        """Get AI provider configuration"""
        return AIProviderConfig(
            gemini_api_key=self.get_env_var('GEMINI_API_KEY'),
            openai_api_key=self.get_env_var('OPENAI_API_KEY')
        )
    
    def get_app_config(self) -> AppConfig:
        """Get application configuration"""
        return AppConfig(
            secret_key=self.get_env_var('APP_SECRET_KEY', ''),
            debug=self.get_env_var('DEBUG', 'False', bool),
            allowed_hosts=self.get_env_var('ALLOWED_HOSTS', [], list),
            closed_alpha_signups=self.get_env_var('CLOSED_ALPHA_SIGN_UPS', [], list),
            require_account_approval=self.get_env_var('REQUIRE_ACCOUNT_APPROVAL', 'False', bool)
        )
    
    def get_url_config(self) -> Dict[str, str]:
        """Get URL configuration"""
        return {
            'api_base_url': self.get_env_var('API_BASE_URL', 'http://localhost:8000/api'),
            'frontend_url': self.get_env_var('FRONTEND_URL', 'http://localhost:3000'),
            'widget_url': self.get_env_var('WIDGET_URL', 'https://widget.ch8r.com')
        }
    
    def get_email_config(self) -> Dict[str, str]:
        """Get email configuration"""
        return {
            'mailersend_api_key': self.get_env_var('MAILERSEND_API_KEY', ''),
            'default_from_email': self.get_env_var('DEFAULT_FROM_EMAIL', ''),
            'discord_signup_webhook_url': self.get_env_var('DISCORD_SIGNUP_WEBHOOK_URL', '')
        }
    
    def get_security_config(self) -> Dict[str, str]:
        """Get security configuration"""
        return {
            'secret_encryption_key': self.get_env_var('SECRET_ENCRYPTION_KEY', ''),
        }

config_manager = ConfigManager()
