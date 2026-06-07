"""Менеджер конфигурации на базе SQLite."""

import json
from pathlib import Path

from app.db.database import DatabaseManager
from app.models.settings import AppSettings
from app.repositories.mailbox_repository import MailboxRepository
from app.repositories.settings_repository import SettingsRepository


class ConfigManager:
    """Единая точка доступа к настройкам и ящикам (SQLite)."""

    def __init__(
        self,
        db: DatabaseManager | None = None,
        legacy_json_path: Path | None = None,
    ) -> None:
        self._db = db or DatabaseManager()
        self._settings = SettingsRepository(self._db)
        self._mailboxes = MailboxRepository(self._db)
        if legacy_json_path is None:
            legacy_json_path = Path(__file__).resolve().parent.parent.parent / "config.json"
        self._legacy_json_path = legacy_json_path
        self._migrate_legacy_json()

    @property
    def db_path(self) -> Path:
        """Путь к файлу SQLite."""
        return self._db.path

    def _migrate_legacy_json(self) -> None:
        """Переносит config.json в SQLite (один раз)."""
        if self._settings.is_json_migrated():
            return

        if self._legacy_json_path.exists():
            try:
                raw = json.loads(self._legacy_json_path.read_text(encoding="utf-8"))
                settings = AppSettings.from_dict(raw)
                if settings.api_key:
                    self._settings.set_api_key(settings.api_key)
                for box in settings.mailboxes:
                    self._mailboxes.upsert_from_dict(box.to_dict())
            except (json.JSONDecodeError, OSError):
                pass

        self._settings.mark_json_migrated()

    def load(self) -> AppSettings:
        """Загружает настройки из БД."""
        return AppSettings(
            api_key=self._settings.get_api_key(),
            mailboxes=self._mailboxes.list_all(),
        )

    def update_api_key(self, api_key: str) -> AppSettings:
        """Обновляет API-ключ (пустая строка = не менять)."""
        if api_key.strip():
            self._settings.set_api_key(api_key.strip())
        return self.load()

    def require_mailbox(self, mailbox_id: str):
        """Возвращает ящик или ValueError."""
        box = self._mailboxes.get_by_id(mailbox_id)
        if not box:
            raise ValueError(f"Ящик {mailbox_id} не найден")
        return box

    def list_mailboxes(self):
        return self._mailboxes.list_all()

    def add_mailbox(self, name: str, email: str):
        return self._mailboxes.create(name, email)

    def update_mailbox(self, mailbox_id: str, name: str, email: str):
        return self._mailboxes.update(mailbox_id, name, email)

    def delete_mailbox(self, mailbox_id: str) -> None:
        self._mailboxes.delete(mailbox_id)

    def public_view(self) -> dict:
        """Публичные настройки для фронтенда."""
        return {
            "has_api_key": self._settings.has_api_key(),
            "api_key_preview": self._settings.api_key_preview(),
            "mailboxes": [b.to_dict() for b in self._mailboxes.list_all()],
            "db_path": str(self._db.path.name),
            "emails_stored": self._settings.get("emails_count", "0"),
        }

    @property
    def settings_repo(self) -> SettingsRepository:
        return self._settings
