Use this command to generate SECRET_ENCRYPTION_KEY:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
