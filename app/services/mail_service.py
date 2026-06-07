"""Бизнес-логика работы с почтой (данные из SQLite + синхронизация Resend)."""

from typing import Any

from fastapi import HTTPException

from app.config.manager import ConfigManager
from app.models.dto import ReplyEmailDto, SendEmailDto
from app.models.mailbox import Mailbox
from app.repositories.email_repository import EmailRepository
from app.services.resend_client import ResendApiClient
from app.services.sync_service import SyncService
from app.services.thread_service import Thread, ThreadService
from app.utils.address_parser import AddressParser
from app.utils.email_helper import EmailHelper


class MailService:
    """Координирует отправку, локальное хранение и цепочки переписки."""

    def __init__(
        self,
        config_manager: ConfigManager,
        resend_client: ResendApiClient,
        email_repository: EmailRepository,
        sync_service: SyncService,
    ) -> None:
        self._config = config_manager
        self._client = resend_client
        self._emails = email_repository
        self._sync = sync_service
        self._parser = AddressParser()
        self._threads = ThreadService()
        self._helper = EmailHelper()

    def _require_mailbox(self, mailbox_id: str) -> Mailbox:
        try:
            box = self._config.require_mailbox(mailbox_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if not box.email:
            raise HTTPException(status_code=400, detail="У ящика не указан email.")
        return box

    @staticmethod
    def _require_body(html: str, text: str, error_message: str) -> None:
        if not html.strip() and not text.strip():
            raise HTTPException(status_code=400, detail=error_message)

    def sync_mailbox(self) -> dict[str, Any]:
        """Синхронизирует письма с Resend в SQLite."""
        return self._sync.sync_all()

    def _emails_from_db(self) -> tuple[list[dict], list[dict]]:
        """Читает входящие и исходящие из локальной БД."""
        return self._emails.list_received(), self._emails.list_sent()

    def _enrich_thread_from_db_or_api(self, thread: Thread) -> None:
        """Дополняет тело письма из БД или Resend API."""
        for msg in thread.messages:
            stored = self._emails.get_by_id(msg.id)
            if stored:
                msg.html = stored.get("html")
                msg.text = stored.get("text")
                if stored.get("message_id"):
                    msg.message_id = stored.get("message_id")
                if stored.get("last_event"):
                    msg.last_event = stored.get("last_event")
                continue
            try:
                if msg.source == "received":
                    full = self._client.get_received(msg.id)
                else:
                    full = self._client.get_sent(msg.id)
                self._emails.upsert_from_api(full, msg.source)
                msg.html = full.get("html")
                msg.text = full.get("text")
                if full.get("message_id"):
                    msg.message_id = full.get("message_id")
            except HTTPException:
                continue

    def _find_thread_fast(self, mailbox: Mailbox, thread_id: str) -> Thread | None:
        received, sent = self._emails_from_db()
        threads = self._threads.build_threads(mailbox, received, sent, include_details=True)
        return next((t for t in threads if t.id == thread_id), None)

    def list_threads(self, mailbox_id: str, sync: bool = True) -> dict[str, Any]:
        """Список цепочек: синхронизация + чтение из SQLite."""
        mailbox = self._require_mailbox(mailbox_id)
        sync_info = self._sync.sync_all() if sync else {"skipped": True}
        received, sent = self._emails_from_db()
        threads = self._threads.build_threads(mailbox, received, sent, include_details=False)
        return {
            "mailbox_id": mailbox_id,
            "threads": [t.to_summary() for t in threads],
            "total": len(threads),
            "sync": sync_info,
        }

    def get_thread(self, mailbox_id: str, thread_id: str) -> dict[str, Any]:
        """Полная цепочка из SQLite."""
        mailbox = self._require_mailbox(mailbox_id)
        thread = self._find_thread_fast(mailbox, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Цепочка не найдена")
        self._enrich_thread_from_db_or_api(thread)
        return thread.to_detail()

    def send_email(self, dto: SendEmailDto) -> dict[str, Any]:
        mailbox = self._require_mailbox(dto.mailbox_id)
        to_list = self._parser.parse(dto.to)
        if not to_list:
            raise HTTPException(status_code=400, detail="Укажите получателя.")
        self._require_body(dto.html, dto.text, "Текст письма не может быть пустым.")

        params: dict[str, Any] = {
            "from": mailbox.from_address(),
            "to": to_list,
            "subject": dto.subject.strip(),
        }
        if dto.html.strip():
            params["html"] = dto.html
        if dto.text.strip():
            params["text"] = dto.text

        cc = self._parser.parse(dto.cc)
        bcc = self._parser.parse(dto.bcc)
        reply_to = self._parser.parse(dto.reply_to)
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc
        if reply_to:
            params["reply_to"] = reply_to

        result = self._client.send(params)
        email_id = result.get("id") if isinstance(result, dict) else None
        if email_id:
            try:
                self._sync.store_sent_by_id(email_id)
            except HTTPException:
                self._emails.upsert_from_api(
                    {
                        "id": email_id,
                        "from": mailbox.from_address(),
                        "to": to_list,
                        "subject": dto.subject,
                        "html": dto.html,
                        "text": dto.text,
                    },
                    "sent",
                )
        return {"ok": True, "data": result}

    def reply_in_thread(
        self,
        mailbox_id: str,
        thread_id: str,
        dto: ReplyEmailDto,
    ) -> dict[str, Any]:
        mailbox = self._require_mailbox(mailbox_id)
        self._require_body(dto.html, dto.text, "Текст ответа не может быть пустым.")

        thread = self._find_thread_fast(mailbox, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Цепочка не найдена")

        if not self._threads.collect_message_ids(thread):
            self._enrich_thread_from_db_or_api(thread)

        recipient = self._resolve_reply_recipient(thread, mailbox)
        subject = self._resolve_reply_subject(thread)
        message_ids = self._threads.collect_message_ids(thread)
        last_id = message_ids[-1] if message_ids else None

        params: dict[str, Any] = {
            "from": mailbox.from_address(),
            "to": [recipient],
            "subject": subject,
        }
        if dto.html.strip():
            params["html"] = dto.html
        if dto.text.strip():
            params["text"] = dto.text

        headers: dict[str, str] = {}
        if last_id:
            headers["In-Reply-To"] = last_id
        if message_ids:
            headers["References"] = " ".join(message_ids)
        if headers:
            params["headers"] = headers

        result = self._client.send(params)
        email_id = result.get("id") if isinstance(result, dict) else None
        if email_id:
            try:
                self._sync.store_sent_by_id(email_id)
            except HTTPException:
                self._emails.upsert_from_api(
                    {
                        "id": email_id,
                        "from": mailbox.from_address(),
                        "to": [recipient],
                        "subject": subject,
                        "html": dto.html,
                        "text": dto.text,
                    },
                    "sent",
                )
        return {"ok": True, "data": result}

    def handle_inbound_webhook(self, payload: dict) -> dict[str, Any]:
        """Обрабатывает webhook ``email.received`` от Resend."""
        if payload.get("type") != "email.received":
            return {"ok": True, "ignored": True}

        data = payload.get("data") or {}
        email_id = data.get("email_id")
        if not email_id:
            raise HTTPException(status_code=400, detail="email_id отсутствует в webhook")

        self._sync.store_received_by_id(email_id)
        return {"ok": True, "stored": email_id}

    @staticmethod
    def _resolve_reply_recipient(thread: Thread, mailbox: Mailbox) -> str:
        box_email = mailbox.email.lower()
        for msg in sorted(thread.messages, key=lambda m: m.created_at, reverse=True):
            if msg.direction == "inbound":
                return msg.from_addr
            for addr in msg.to_addrs:
                if EmailHelper.extract_email(addr) != box_email:
                    return addr
        if thread.participants:
            return thread.participants[0]
        raise HTTPException(status_code=400, detail="Не удалось определить получателя.")

    @staticmethod
    def _resolve_reply_subject(thread: Thread) -> str:
        raw = thread.messages[0].subject if thread.messages else thread.subject
        if raw.lower().startswith("re:"):
            return raw
        return f"Re: {raw}"
