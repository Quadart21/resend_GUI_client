"""Контроллер webhook Resend."""

from fastapi import APIRouter, Request

from app.services.auth_service import AuthService, SESSION_COOKIE
from app.services.mail_service import MailService


class WebhookController:
    """Принимает входящие события Resend (email.received)."""

    def __init__(self, mail_service: MailService, auth_service: AuthService) -> None:
        self._mail = mail_service
        self._auth = auth_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.post("/webhooks/resend")
        async def resend_webhook(request: Request) -> dict:
            # Webhook от Resend — без cookie-сессии
            payload = await request.json()
            return self._mail.handle_inbound_webhook(payload)

        @router.post("/sync")
        async def manual_sync(request: Request) -> dict:
            self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            return self._mail.sync_mailbox()
