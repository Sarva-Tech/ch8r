from cryptography.fernet import Fernet
from config.settings import SECRET_ENCRYPTION_KEY
import json

key = SECRET_ENCRYPTION_KEY
if not key:
    raise ValueError("Missing SECRET_ENCRYPTION_KEY in settings")

fernet = Fernet(key.encode())

def encrypt_dict(data: dict) -> str:
    if not data:
        return json.dumps({})
    encrypted = {k: fernet.encrypt(str(v).encode()).decode() for k, v in data.items()}
    return json.dumps(encrypted)

def decrypt_dict(encrypted: str) -> dict:
    try:
        data = json.loads(encrypted)
        decrypted = {k: fernet.decrypt(v.encode()).decode() for k, v in data.items()}
        return decrypted
    except Exception:
        return {}
