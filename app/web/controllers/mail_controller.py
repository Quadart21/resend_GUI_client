"""Контроллер операций с почтой."""

from fastapi import APIRouter

from app.models.dto import ReplyEmailDto, SendEmailDto
from app.services.mail_service import MailService


class MailController:
    """REST API для отправки и получения писем."""

    def __init__(self, mail_service: MailService) -> None:
        self._mail = mail_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.post("/emails/send")
        async def send_email(body: SendEmailDto) -> dict:
            return self._mail.send_email(body)

        @router.get("/emails/sent")
        async def list_sent(after: str | None = None) -> dict:
            return self._mail.list_sent(after)

        @router.get("/emails/sent/{email_id}")
        async def get_sent(email_id: str) -> dict:
            return self._mail.get_sent(email_id)

        @router.get("/emails/received")
        async def list_received(after: str | None = None) -> dict:
            return self._mail.list_received(after)

        @router.get("/emails/received/{email_id}")
        async def get_received(email_id: str) -> dict:
            return self._mail.get_received(email_id)

        @router.post("/emails/received/{email_id}/reply")
        async def reply_to_received(email_id: str, body: ReplyEmailDto) -> dict:
            return self._mail.reply_to_received(email_id, body)
