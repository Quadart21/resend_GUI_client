"""Менеджер локального хранения настроек."""

import json
from pathlib import Path

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

    def update(self, api_key: str | None = None, from_email: str | None = None, from_name: str | None = None) -> AppSettings:
        """
        Обновляет отдельные поля настроек.

        Если ``api_key`` передан как пустая строка, существующий ключ сохраняется.
        """
        current = self.load()

        if from_email is not None:
            current.from_email = from_email.strip()
        if from_name is not None:
            current.from_name = from_name.strip()
        if api_key is not None and api_key.strip():
            current.api_key = api_key.strip()

        return self.save(current)

    def public_view(self) -> dict:
        """Возвращает настройки без полного API-ключа (для фронтенда)."""
        settings = self.load()
        return {
            "from_email": settings.from_email,
            "from_name": settings.from_name,
            "has_api_key": settings.has_api_key(),
            "api_key_preview": settings.api_key_preview(),
        }
