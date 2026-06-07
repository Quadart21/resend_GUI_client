"""Менеджер локального хранения настроек."""

import json
import uuid
from pathlib import Path

from app.models.mailbox import MAILBOX_COLORS, Mailbox
from app.models.settings import AppSettings


class ConfigManager:
    """Читает и сохраняет настройки приложения в JSON-файл."""

    def __init__(self, config_path: Path | None = None) -> None:
        """
        :param config_path: Путь к config.json. По умолчанию — рядом с корнем проекта.
        """
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent.parent / "config.json"
        self._path = config_path

    @property
    def path(self) -> Path:
        """Путь к файлу конфигурации."""
        return self._path

    def load(self) -> AppSettings:
        """Загружает настройки с диска или возвращает значения по умолчанию."""
        if not self._path.exists():
            return AppSettings()

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return AppSettings.from_dict(raw)
        except (json.JSONDecodeError, OSError):
            return AppSettings()

    def save(self, settings: AppSettings) -> AppSettings:
        """Сохраняет настройки на диск."""
        self._path.write_text(
            json.dumps(settings.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return settings

    def update_api_key(self, api_key: str) -> AppSettings:
        """
        Обновляет API-ключ.

        Пустая строка означает «не менять».
        """
        current = self.load()
        if api_key.strip():
            current.api_key = api_key.strip()
        return self.save(current)

    def require_mailbox(self, mailbox_id: str) -> Mailbox:
        """Возвращает ящик или выбрасывает ValueError."""
        box = self.load().get_mailbox(mailbox_id)
        if not box:
            raise ValueError(f"Ящик {mailbox_id} не найден")
        return box

    def list_mailboxes(self) -> list[Mailbox]:
        """Список всех ящиков."""
        return self.load().mailboxes

    def add_mailbox(self, name: str, email: str) -> Mailbox:
        """Добавляет новый почтовый ящик."""
        settings = self.load()
        email = email.strip().lower()
        for box in settings.mailboxes:
            if box.email == email:
                raise ValueError(f"Ящик {email} уже существует")

        color = MAILBOX_COLORS[len(settings.mailboxes) % len(MAILBOX_COLORS)]
        new_box = Mailbox(id=str(uuid.uuid4()), name=name.strip(), email=email, color=color)
        settings.mailboxes.append(new_box)
        self.save(settings)
        return new_box

    def update_mailbox(self, mailbox_id: str, name: str, email: str) -> Mailbox:
        """Обновляет существующий ящик."""
        settings = self.load()
        email = email.strip().lower()
        target: Mailbox | None = None

        for box in settings.mailboxes:
            if box.id != mailbox_id and box.email == email:
                raise ValueError(f"Ящик {email} уже существует")

        for box in settings.mailboxes:
            if box.id == mailbox_id:
                box.name = name.strip()
                box.email = email
                target = box
                break

        if not target:
            raise ValueError(f"Ящик {mailbox_id} не найден")

        self.save(settings)
        return target

    def delete_mailbox(self, mailbox_id: str) -> None:
        """Удаляет ящик по ID."""
        settings = self.load()
        settings.mailboxes = [b for b in settings.mailboxes if b.id != mailbox_id]
        self.save(settings)

    def public_view(self) -> dict:
        """Возвращает настройки без полного API-ключа (для фронтенда)."""
        settings = self.load()
        return {
            "has_api_key": settings.has_api_key(),
            "api_key_preview": settings.api_key_preview(),
            "mailboxes": [box.to_dict() for box in settings.mailboxes],
        }
