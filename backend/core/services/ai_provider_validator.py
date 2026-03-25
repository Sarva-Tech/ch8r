from typing import Tuple, Dict, Any

from core.models import AIProvider
from .factories.ai_provider_factory import AIProviderFactory


class AIProviderValidator:
    """Validates AI provider configurations"""
    
    def __init__(self):
        self.provider_factory = AIProviderFactory()
    
    def validate_provider_config(
        self, 
        provider_type: str, 
        api_key: str, 
        config: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """
        Validate AI provider configuration
        
        Args:
            provider_type: Type of AI provider
            api_key: API key for the provider
            config: Additional configuration
            
        Returns:
            Tuple of (is_valid, provider_models)
        """
        try:
            return self.provider_factory.validate_provider(
                provider_type=provider_type,
                api_key=api_key,
                config=config
            )
        except Exception as e:
            return False, str(e)
    
    def validate_ai_provider_data(
        self, 
        validated_data: Dict[str, Any], 
        instance: AIProvider = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Prepare and validate AI provider data
        
        Args:
            validated_data: Validated serializer data
            instance: Existing AI provider instance (for updates)
            
        Returns:
            Tuple of (main_fields, config_data)
        """
        main_fields = ['name', 'provider', 'provider_api_key']
        config = {}
        
        if instance:
            current_data = {
                'name': instance.name,
                'provider': instance.provider,
                'provider_api_key': instance.provider_api_key
            }
            if instance.metadata:
                config.update(instance.metadata)
            update_data = {**current_data, **validated_data}
            if not update_data['provider_api_key']:
                update_data['provider_api_key'] = instance.provider_api_key
            validation_data = update_data
        else:
            validation_data = validated_data
        
        main_data = {}
        for field, value in validation_data.items():
            if field in main_fields:
                main_data[field] = value
            else:
                config[field] = str(value).strip() if value is not None else ''
        
        return main_data, config
