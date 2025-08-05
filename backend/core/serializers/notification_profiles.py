from rest_framework import serializers
from core.models import NotificationProfile
from core.services import decrypt_with_private_key
from core.services.encryption import encrypt_dict


class NotificationProfileSerializer(serializers.ModelSerializer):
    config = serializers.JSONField(binary=True)  # Critical change for JSONB

    class Meta:
        model = NotificationProfile
        fields = ['id', 'type', 'config', 'created_at', 'name']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        config = validated_data.pop('config', {})
        instance = NotificationProfile(**validated_data)
        instance._config = encrypt_dict(config)  # Your existing encryption
        instance.save()
        return instance

class BulkNotificationProfileSerializer(serializers.ModelSerializer):
    config = serializers.JSONField()

    class Meta:
        model = NotificationProfile
        fields = ['name', 'type', 'config']

def create(self, validated_data):
    encrypted_config = validated_data.get('config')

    # Defensive: if config is string (sometimes might be), parse it
    if isinstance(encrypted_config, str):
        try:
            encrypted_config = json.loads(encrypted_config)
        except Exception:
            raise serializers.ValidationError("Config field must be a JSON object")

    if not isinstance(encrypted_config, dict):
        raise serializers.ValidationError("Config field must be a dictionary")

    decrypted_config = {}

    for key, value in encrypted_config.items():
        if isinstance(value, str):
            try:
                decrypted_value = decrypt_with_private_key(value)
                decrypted_config[key] = decrypted_value
            except Exception as e:
                raise serializers.ValidationError(f"Failed to decrypt '{key}': {str(e)}")
        else:
            # If value is not string, you can decide to keep or reject
            decrypted_config[key] = value

    encrypted_config_dict = encrypt_dict(decrypted_config)

    instance = NotificationProfile(
        name=validated_data['name'],
        type=validated_data['type'],
        config=encrypted_config_dict
    )
    instance.save()
    return instance
