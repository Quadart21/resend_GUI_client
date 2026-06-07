"""Хеширование паролей (PBKDF2, без внешних зависимостей)."""

import hashlib
import secrets


class PasswordService:
    """Создание и проверка хешей паролей."""

    _ITERATIONS = 120_000

    @classmethod
    def hash_password(cls, password: str) -> str:
        """Возвращает строку ``salt$hexhash``."""
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            cls._ITERATIONS,
        )
        return f"{salt}${digest.hex()}"

    @classmethod
    def verify_password(cls, password: str, stored: str) -> bool:
        """Сравнивает пароль с сохранённым хешем."""
        try:
            salt, expected = stored.split("$", 1)
        except ValueError:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            cls._ITERATIONS,
        )
        return secrets.compare_digest(digest.hex(), expected)
