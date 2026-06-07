"""Контроллер управления почтовыми ящиками."""

from fastapi import APIRouter, HTTPException, Request

from app.config.manager import ConfigManager
from app.models.dto import MailboxCreateDto, MailboxUpdateDto
from app.services.auth_service import AuthService, SESSION_COOKIE


class MailboxController:
    """REST API для CRUD почтовых ящиков."""

    def __init__(self, config_manager: ConfigManager, auth_service: AuthService) -> None:
        self._config = config_manager
        self._auth = auth_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/mailboxes")
        async def list_mailboxes(request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            boxes = self._config.list_mailboxes_for_user(user)
            return {"mailboxes": [b.to_dict() for b in boxes]}

        @router.post("/mailboxes")
        async def create_mailbox(body: MailboxCreateDto, request: Request) -> dict:
            self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            try:
                box = self._config.add_mailbox(body.name, body.email)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"ok": True, "mailbox": box.to_dict()}

        @router.put("/mailboxes/{mailbox_id}")
        async def update_mailbox(mailbox_id: str, body: MailboxUpdateDto, request: Request) -> dict:
            self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            try:
                box = self._config.update_mailbox(mailbox_id, body.name, body.email)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"ok": True, "mailbox": box.to_dict()}

        @router.delete("/mailboxes/{mailbox_id}")
        async def delete_mailbox(mailbox_id: str, request: Request) -> dict:
            self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            self._config.delete_mailbox(mailbox_id)
            return {"ok": True}
