"""Контроллер управления почтовыми ящиками."""

from fastapi import APIRouter, HTTPException

from app.config.manager import ConfigManager
from app.models.dto import MailboxCreateDto, MailboxUpdateDto


class MailboxController:
    """REST API для CRUD почтовых ящиков."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/mailboxes")
        async def list_mailboxes() -> dict:
            boxes = self._config.list_mailboxes()
            return {"mailboxes": [b.to_dict() for b in boxes]}

        @router.post("/mailboxes")
        async def create_mailbox(body: MailboxCreateDto) -> dict:
            try:
                box = self._config.add_mailbox(body.name, body.email)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"ok": True, "mailbox": box.to_dict()}

        @router.put("/mailboxes/{mailbox_id}")
        async def update_mailbox(mailbox_id: str, body: MailboxUpdateDto) -> dict:
            try:
                box = self._config.update_mailbox(mailbox_id, body.name, body.email)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"ok": True, "mailbox": box.to_dict()}

        @router.delete("/mailboxes/{mailbox_id}")
        async def delete_mailbox(mailbox_id: str) -> dict:
            self._config.delete_mailbox(mailbox_id)
            return {"ok": True}
