"""Контроллер операций с почтой и цепочками."""

from fastapi import APIRouter

from app.models.dto import ReplyEmailDto, SendEmailDto
from app.services.mail_service import MailService


class MailController:
    """REST API для отправки писем и цепочек переписки."""

    def __init__(self, mail_service: MailService) -> None:
        self._mail = mail_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/mailboxes/{mailbox_id}/threads")
        async def list_threads(mailbox_id: str) -> dict:
            return self._mail.list_threads(mailbox_id)

        @router.get("/mailboxes/{mailbox_id}/threads/{thread_id}")
        async def get_thread(mailbox_id: str, thread_id: str) -> dict:
            return self._mail.get_thread(mailbox_id, thread_id)

        @router.post("/emails/send")
        async def send_email(body: SendEmailDto) -> dict:
            return self._mail.send_email(body)

        @router.post("/mailboxes/{mailbox_id}/threads/{thread_id}/reply")
        async def reply_in_thread(mailbox_id: str, thread_id: str, body: ReplyEmailDto) -> dict:
            return self._mail.reply_in_thread(mailbox_id, thread_id, body)
