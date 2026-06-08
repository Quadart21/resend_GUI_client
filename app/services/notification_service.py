"""Проверка новых входящих для браузерных уведомлений."""

from datetime import datetime, timezone

from app.config.manager import ConfigManager
from app.models.user import User
from app.repositories.email_flags_repository import EmailFlagsRepository
from app.repositories.email_repository import EmailRepository


class NotificationService:
    """Возвращает новые входящие письма для доступных пользователю ящиков."""

    def __init__(
        self,
        config_manager: ConfigManager,
        email_repository: EmailRepository,
        email_flags_repository: EmailFlagsRepository,
    ) -> None:
        self._config = config_manager
        self._emails = email_repository
        self._flags = email_flags_repository

    def check_inbound(self, user: User, since: str) -> dict:
        """
        Список входящих после ``since`` (ISO UTC).

        Клиент опрашивает endpoint и показывает системное уведомление.
        """
        mailboxes = self._config.list_mailboxes_for_user(user)
        mailbox_emails = [b.email for b in mailboxes]
        deleted = self._flags.list_deleted_ids(user.id)
        items = self._emails.list_inbound_since(since, mailbox_emails, deleted)
        return {
            "items": items,
            "server_time": datetime.now(timezone.utc).isoformat(),
        }
