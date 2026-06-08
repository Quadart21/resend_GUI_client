"""Контроллер операций с почтой и цепочками."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.models.dto import ReplyEmailDto, SendEmailDto, StarDto
from app.services.auth_service import AuthService, SESSION_COOKIE
from app.services.mail_service import MailService


class MailController:
    """REST API для отправки писем и цепочек переписки."""

    def __init__(self, mail_service: MailService, auth_service: AuthService) -> None:
        self._mail = mail_service
        self._auth = auth_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/mailboxes/unread-counts")
        async def unread_counts(request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            return {"counts": self._mail.unread_counts_for_user(user)}

        @router.get("/mailboxes/{mailbox_id}/threads")
        async def list_threads(
            mailbox_id: str,
            request: Request,
            sync: bool = False,
            email_limit: int = 500,
        ) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.list_threads(
                mailbox_id, user.id, sync=sync, email_limit=email_limit
            )

        @router.get("/search/threads")
        async def search_threads(request: Request, q: str = "", limit: int = 50) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            return self._mail.search_threads(user, q, limit=limit)

        @router.get("/mailboxes/{mailbox_id}/threads/{thread_id}")
        async def get_thread(mailbox_id: str, thread_id: str, request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.get_thread(mailbox_id, thread_id, user.id)

        @router.post("/mailboxes/{mailbox_id}/threads/read-all")
        async def mark_all_read(mailbox_id: str, request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.mark_all_threads_read(mailbox_id, user.id)

        @router.post("/mailboxes/{mailbox_id}/threads/{thread_id}/read")
        async def mark_thread_read(mailbox_id: str, thread_id: str, request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.mark_thread_read(mailbox_id, thread_id, user.id)

        @router.post("/mailboxes/{mailbox_id}/threads/{thread_id}/star")
        async def star_thread(
            mailbox_id: str,
            thread_id: str,
            body: StarDto,
            request: Request,
        ) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.star_thread(mailbox_id, thread_id, user.id, body.starred)

        @router.post("/mailboxes/{mailbox_id}/emails/{email_id}/star")
        async def star_email(
            mailbox_id: str,
            email_id: str,
            body: StarDto,
            request: Request,
        ) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.star_email(mailbox_id, email_id, user.id, body.starred)

        @router.delete("/mailboxes/{mailbox_id}/emails/{email_id}")
        async def delete_email(mailbox_id: str, email_id: str, request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            return self._mail.delete_email(mailbox_id, email_id, user.id)

        @router.get("/mailboxes/{mailbox_id}/emails/{email_id}/attachments/{attachment_id}")
        async def download_attachment(
            mailbox_id: str,
            email_id: str,
            attachment_id: str,
            request: Request,
        ):
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            self._auth.require_mailbox_access(user, mailbox_id)
            data = self._mail.get_attachment_download(
                mailbox_id, email_id, attachment_id, user.id
            )
            return RedirectResponse(data["download_url"], status_code=302)

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
            return self._mail.reply_in_thread(mailbox_id, thread_id, body, user.id)
