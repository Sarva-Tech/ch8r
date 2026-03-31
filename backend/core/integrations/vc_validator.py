from core.services.providers.version_control import VCProviderRegistry


def validate_vc_credentials(provider_name: str, credentials: dict) -> tuple[bool, str, dict]:
    try:
        if not VCProviderRegistry.is_registered(provider_name):
            return False, f"Unknown provider: {provider_name}", {}

        provider = VCProviderRegistry.get_provider(provider_name, credentials)
        return provider.validate_credentials()
    except Exception as e:
        return False, str(e), {}
