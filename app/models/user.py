"""Модель пользователя системы."""

from dataclasses import dataclass, field


@dataclass
class User:
    """Пользователь с правами доступа к ящикам."""

    id: str
    username: str
    is_admin: bool = False
    is_active: bool = True
    mailbox_ids: list[str] = field(default_factory=list)

    def to_public_dict(self) -> dict:
        """Публичное представление для API (без пароля)."""
        return {
            "id": self.id,
            "username": self.username,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "mailbox_ids": self.mailbox_ids,
        }

    def can_access_mailbox(self, mailbox_id: str) -> bool:
        """Админ видит все ящики; обычный пользователь — только назначенные."""
        if self.is_admin:
            return True
        return mailbox_id in self.mailbox_ids
