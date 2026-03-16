from django.db import models
from cryptography.fernet import Fernet, InvalidToken
import json
from config import settings

fernet = Fernet(settings.SECRET_ENCRYPTION_KEY)


class EncryptedCharField(models.CharField):
    def get_prep_value(self, value):
        if value:
            return fernet.encrypt(value.encode()).decode()
        return value

    def from_db_value(self, value, expression, connection):
        if value:
            return fernet.decrypt(value.encode()).decode()
        return value


class EncryptedJSONField(models.TextField):
    def get_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, str):
            # Ensure it's valid JSON before encrypting
            value = json.loads(value)
        return fernet.encrypt(json.dumps(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None:
            return None
        try:
            decrypted = fernet.decrypt(value.encode()).decode()
            return json.loads(decrypted)
        except Exception:
            # Legacy plain JSON (stored before encryption was added)
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return {}

    def to_python(self, value):
        if value is None or isinstance(value, dict):
            return value
        if isinstance(value, str):
            return json.loads(value)
        return value
