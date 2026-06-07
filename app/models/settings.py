"""Модель настроек приложения."""

from dataclasses import dataclass, field

from app.models.mailbox import MAILBOX_COLORS, Mailbox


@dataclass
class AppSettings:
    """Локальные настройки почтового клиента."""

    api_key: str = ""
    mailboxes: list[Mailbox] = field(default_factory=list)

    def has_api_key(self) -> bool:
        """Проверяет, задан ли API-ключ Resend."""
        return bool(self.api_key.strip())

    def api_key_preview(self) -> str:
        """Возвращает маскированный префикс ключа для отображения в UI."""
        if not self.api_key:
            return ""
        return self.api_key[:8] + "..."

    def get_mailbox(self, mailbox_id: str) -> Mailbox | None:
        """Находит ящик по ID."""
        for box in self.mailboxes:
            if box.id == mailbox_id:
                return box
        return None

    def to_dict(self) -> dict:
        """Сериализует настройки в словарь."""
        return {
            "api_key": self.api_key,
            "mailboxes": [box.to_dict() for box in self.mailboxes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        """
        Создаёт объект настроек из словаря.

        Поддерживает миграцию со старого формата (from_email / from_name).
        """
        mailboxes: list[Mailbox] = []

        if data.get("mailboxes"):
            for item in data["mailboxes"]:
                mailboxes.append(Mailbox.from_dict(item))
        elif data.get("from_email"):
            # Миграция: один ящик из старых полей
            mailboxes.append(
                Mailbox(
                    name=str(data.get("from_name", "")).strip(),
                    email=str(data.get("from_email", "")).strip().lower(),
                    color=MAILBOX_COLORS[0],
                )
            )

        return cls(
            api_key=str(data.get("api_key", "")).strip(),
            mailboxes=mailboxes,
        )
