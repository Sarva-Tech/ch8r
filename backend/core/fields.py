from django.db import models
from cryptography.fernet import Fernet
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
