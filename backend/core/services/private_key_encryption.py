import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY_PEM = os.getenv('PRIVATE_KEY')

def decrypt_with_private_key(encrypted_data: str) -> str:
    if not PRIVATE_KEY_PEM:
        raise ValueError("Missing PRIVATE_KEY in environment")

    private_key = serialization.load_pem_private_key(
        PRIVATE_KEY_PEM.encode(),
        password=None,
        backend=default_backend()
    )

    decrypted_data = private_key.decrypt(
        base64.b64decode(encrypted_data),
        padding=padding.PKCS1v15()
    )

    return decrypted_data.decode()
