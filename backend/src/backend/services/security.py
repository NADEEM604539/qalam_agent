import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise RuntimeError(
        "ENCRYPTION_KEY is not configured"
    )

fernet = Fernet(
    ENCRYPTION_KEY.encode()
)


def encrypt_password(password: str) -> str:

    encrypted = fernet.encrypt(
        password.encode()
    )

    return encrypted.decode()


def decrypt_password(
    encrypted_password: str
) -> str:

    decrypted = fernet.decrypt(
        encrypted_password.encode()
    )

    return decrypted.decode()