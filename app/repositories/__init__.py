"""Репозитории для работы с SQLite."""

from app.repositories.email_repository import EmailRepository
from app.repositories.mailbox_repository import MailboxRepository
from app.repositories.settings_repository import SettingsRepository

__all__ = ["EmailRepository", "MailboxRepository", "SettingsRepository"]
