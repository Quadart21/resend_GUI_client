"""Контроллер webhook Resend."""

from fastapi import APIRouter, Request

from app.services.mail_service import MailService


class WebhookController:
    """Принимает входящие события Resend (email.received)."""

    def __init__(self, mail_service: MailService) -> None:
        self._mail = mail_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.post("/webhooks/resend")
        async def resend_webhook(request: Request) -> dict:
            payload = await request.json()
            return self._mail.handle_inbound_webhook(payload)

        @router.post("/sync")
        async def manual_sync() -> dict:
            return self._mail.sync_mailbox()
