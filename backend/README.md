Use this command to generate SECRET_ENCRYPTION_KEY:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

# RSA Public and Private Key Generation Guide


## Step 1: Generate the Private Key

### ➤ Generate a 2048-bit Private Key (commonly used)
```bash
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
```

##  Step 2: Extract the Public Key from the Private Key

```bash
openssl rsa -pubout -in private_key.pem -out public_key.pem
```

### View private key:
```bash
cat private_key.pem
```

### View public key:
```bash
cat public_key.pem
```

---

##  Output Examples

### private_key.pem
```
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BA...
-----END PRIVATE KEY-----
```

### public_key.pem
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOC...
-----END PUBLIC KEY-----
```
