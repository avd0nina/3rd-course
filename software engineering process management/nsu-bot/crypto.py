import os
from cryptography.fernet import Fernet


def generate_key() -> str:
    # Генерирует новый ключ шифрования — запустить один раз и сохранить в .env
    return Fernet.generate_key().decode()


def _get_fernet() -> Fernet:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY не задан в .env")
    return Fernet(key.encode())


def encrypt(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()


if __name__ == "__main__":
    generate_key()
    print("Сгенерирован ключ для ENCRYPTION_KEY")
