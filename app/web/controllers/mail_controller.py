"""Контроллер операций с почтой и цепочками."""

from fastapi import APIRouter, HTTPException, Request

from app.models.dto import ReplyEmailDto, SendEmailDto
from app.services.auth_service import AuthService, SESSION_COOKIE
from app.services.mail_service import MailService


class MailController:
    """REST API для отправки писем и цепочек переписки."""

    def __init__(self, mail_service: MailService, auth_service: AuthService) -> None:
        self._mail = mail_service
        self._auth = auth_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/mailboxes/{mailbox_id}/threads")
        async def list_threads(mailbox_id: str, request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.list_threads(mailbox_id)

        @router.get("/mailboxes/{mailbox_id}/threads/{thread_id}")
        async def get_thread(mailbox_id: str, thread_id: str, request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.get_thread(mailbox_id, thread_id)

        @router.post("/emails/send")
        async def send_email(body: SendEmailDto, request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, body.mailbox_id)
            return self._mail.send_email(body)

        @router.post("/mailboxes/{mailbox_id}/threads/{thread_id}/reply")
        async def reply_in_thread(
            mailbox_id: str,
            thread_id: str,
            body: ReplyEmailDto,
            request: Request,
        ) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            if body.mailbox_id != mailbox_id:
                raise HTTPException(status_code=400, detail="mailbox_id не совпадает")
            return self._mail.reply_in_thread(mailbox_id, thread_id, body)
