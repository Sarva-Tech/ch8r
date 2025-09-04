from config.settings import SECRET_ENCRYPTION_KEY
from cryptography.fernet import Fernet
import base64
import json
from datetime import datetime, timedelta

key = SECRET_ENCRYPTION_KEY

def encrypt(data: dict | str) -> str:
    if not key:
        raise ValueError("Missing SECRET_ENCRYPTION_KEY in settings")

    fernet = Fernet(key.encode())

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
    if not key:
        raise ValueError("Missing SECRET_ENCRYPTION_KEY in settings")

    fernet = Fernet(key.encode())

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


def _get_fernet():
    if not key:
        raise ValueError("Missing SECRET_ENCRYPTION_KEY in settings")
    return Fernet(key.encode())


def generate_verification_token(user_id, email):
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": (datetime.now() + timedelta(hours=24)).isoformat(),
    }
    payload_str = json.dumps(payload)

    f = _get_fernet()
    token = f.encrypt(payload_str.encode())

    return base64.urlsafe_b64encode(token).decode()


def verify_verification_token(token):
    try:
        token_bytes = base64.urlsafe_b64decode(token.encode())

        f = _get_fernet()
        payload_str = f.decrypt(token_bytes).decode()

        payload = json.loads(payload_str)

        exp_time = datetime.fromisoformat(payload["exp"])
        if datetime.now() > exp_time:
            return None, "Token has expired"

        return payload, None

    except Exception as e:
        return None, f"Invalid token: {str(e)}"