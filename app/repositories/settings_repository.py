"""Репозиторий настроек приложения (ключ API и служебные флаги)."""

from app.db.database import DatabaseManager


class SettingsRepository:
    """Хранит пары key/value в таблице app_settings."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get(self, key: str, default: str = "") -> str:
        """Читает значение по ключу."""
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        """Записывает или обновляет значение."""
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            conn.commit()

    def get_api_key(self) -> str:
        return self.get("api_key")

    def set_api_key(self, api_key: str) -> None:
        self.set("api_key", api_key)

    def has_api_key(self) -> bool:
        return bool(self.get_api_key().strip())

    def api_key_preview(self) -> str:
        key = self.get_api_key()
        if not key:
            return ""
        return key[:8] + "..."

    def get_webhook_secret(self) -> str:
        return self.get("webhook_secret")

    def set_webhook_secret(self, secret: str) -> None:
        self.set("webhook_secret", secret)

    def has_webhook_secret(self) -> bool:
        return bool(self.get_webhook_secret().strip())

    def webhook_secret_preview(self) -> str:
        secret = self.get_webhook_secret()
        if not secret:
            return ""
        return secret[:10] + "..."

    def is_json_migrated(self) -> bool:
        return self.get("migrated_from_json") == "1"

    def mark_json_migrated(self) -> None:
        self.set("migrated_from_json", "1")
