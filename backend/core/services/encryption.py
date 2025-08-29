from cryptography.fernet import Fernet
from config.settings import SECRET_ENCRYPTION_KEY
import json

key = SECRET_ENCRYPTION_KEY
if not key:
    raise ValueError("Missing SECRET_ENCRYPTION_KEY in settings")

fernet = Fernet(key.encode())

def encrypt(data: dict | str) -> str:
    if isinstance(data, dict):
        if not data:
            return json.dumps({})
        encrypted = {k: fernet.encrypt(str(v).encode()).decode() for k, v in data.items()}
        return json.dumps(encrypted)

    elif isinstance(data, str):
        return fernet.encrypt(data.encode()).decode()

    else:
        raise TypeError("Data must be a dict or str")

def decrypt(data: str) -> dict | str:
    try:
        obj = json.loads(data)
        if isinstance(obj, dict):
            return {k: fernet.decrypt(v.encode()).decode() for k, v in obj.items()}
    except Exception:
        pass

    try:
        return fernet.decrypt(data.encode()).decode()
    except Exception:
        return {}
