"""Бизнес-логика работы с почтой."""

from typing import Any

from fastapi import HTTPException

from app.config.manager import ConfigManager
from app.models.dto import ReplyEmailDto, SendEmailDto
from app.models.mailbox import Mailbox
from app.services.resend_client import ResendApiClient
from app.services.thread_service import Thread, ThreadService
from app.utils.address_parser import AddressParser
from app.utils.email_helper import EmailHelper


class MailService:
    """Координирует отправку, получение, ящики и цепочки переписки."""

    def __init__(self, config_manager: ConfigManager, resend_client: ResendApiClient) -> None:
        self._config = config_manager
        self._client = resend_client
        self._parser = AddressParser()
        self._threads = ThreadService()
        self._helper = EmailHelper()

    def _require_mailbox(self, mailbox_id: str) -> Mailbox:
        """Возвращает ящик или HTTP 404."""
        try:
            box = self._config.require_mailbox(mailbox_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if not box.email:
            raise HTTPException(status_code=400, detail="У ящика не указан email.")
        return box

    @staticmethod
    def _require_body(html: str, text: str, error_message: str) -> None:
        """Проверяет, что тело письма не пустое."""
        if not html.strip() and not text.strip():
            raise HTTPException(status_code=400, detail=error_message)

    def _fetch_all_received(self, max_pages: int = 5) -> list[dict]:
        """Загружает входящие письма с пагинацией."""
        items: list[dict] = []
        after: str | None = None
        for _ in range(max_pages):
            result = self._client.list_received(after)
            batch = result.get("data") or []
            items.extend(batch)
            if not result.get("has_more") or not batch:
                break
            after = batch[-1]["id"]
        return items

    def _fetch_all_sent(self, max_pages: int = 5) -> list[dict]:
        """Загружает отправленные письма с пагинацией."""
        items: list[dict] = []
        after: str | None = None
        for _ in range(max_pages):
            result = self._client.list_sent(after)
            batch = result.get("data") or []
            items.extend(batch)
            if not result.get("has_more") or not batch:
                break
            after = batch[-1]["id"]
        return items

    def _enrich_received(self, items: list[dict]) -> list[dict]:
        """Подгружает полное содержимое входящих (для цепочки)."""
        enriched: list[dict] = []
        for item in items:
            try:
                full = self._client.get_received(item["id"])
                enriched.append(full)
            except HTTPException:
                enriched.append(item)
        return enriched

    def _enrich_sent(self, items: list[dict]) -> list[dict]:
        """Подгружает полное содержимое отправленных."""
        enriched: list[dict] = []
        for item in items:
            try:
                full = self._client.get_sent(item["id"])
                enriched.append(full)
            except HTTPException:
                enriched.append(item)
        return enriched

    def list_threads(self, mailbox_id: str) -> dict[str, Any]:
        """Список цепочек переписки для ящика."""
        mailbox = self._require_mailbox(mailbox_id)
        received = self._fetch_all_received()
        sent = self._fetch_all_sent()
        threads = self._threads.build_threads(mailbox, received, sent, include_details=False)
        return {
            "mailbox_id": mailbox_id,
            "threads": [t.to_summary() for t in threads],
            "total": len(threads),
        }

    def get_thread(self, mailbox_id: str, thread_id: str) -> dict[str, Any]:
        """Полная цепочка с содержимым всех писем."""
        mailbox = self._require_mailbox(mailbox_id)
        received = self._enrich_received(self._fetch_all_received())
        sent = self._enrich_sent(self._fetch_all_sent())
        thread = self._threads.find_thread(mailbox, thread_id, received, sent)
        if not thread:
            raise HTTPException(status_code=404, detail="Цепочка не найдена")
        return thread.to_detail()

    def send_email(self, dto: SendEmailDto) -> dict[str, Any]:
        """Отправляет новое письмо от имени выбранного ящика."""
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
        return {"ok": True, "data": result}

    def reply_in_thread(
        self,
        mailbox_id: str,
        thread_id: str,
        dto: ReplyEmailDto,
    ) -> dict[str, Any]:
        """Отвечает в цепочке с корректными In-Reply-To и References."""
        mailbox = self._require_mailbox(mailbox_id)
        self._require_body(dto.html, dto.text, "Текст ответа не может быть пустым.")

        received = self._enrich_received(self._fetch_all_received())
        sent = self._enrich_sent(self._fetch_all_sent())
        thread = self._threads.find_thread(mailbox, thread_id, received, sent)
        if not thread:
            raise HTTPException(status_code=404, detail="Цепочка не найдена")

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
        return {"ok": True, "data": result}

    @staticmethod
    def _resolve_reply_recipient(thread: Thread, mailbox: Mailbox) -> str:
        """Определяет адрес получателя ответа."""
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
        """Формирует тему ответа."""
        raw = thread.messages[0].subject if thread.messages else thread.subject
        if raw.lower().startswith("re:"):
            return raw
        return f"Re: {raw}"
