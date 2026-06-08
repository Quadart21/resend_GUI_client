"""Бизнес-логика работы с почтой (данные из SQLite + синхронизация Resend)."""

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.config.manager import ConfigManager
from app.models.dto import AttachmentDto, ReplyEmailDto, SendEmailDto
from app.models.mailbox import Mailbox
from app.repositories.email_repository import EmailRepository
from app.repositories.email_flags_repository import EmailFlagsRepository
from app.repositories.read_state_repository import ReadStateRepository
from app.services.resend_client import ResendApiClient
from app.services.sync_service import SyncService
from app.services.thread_service import Thread, ThreadService
from app.utils.address_parser import AddressParser
from app.utils.email_helper import EmailHelper


class MailService:
    """Координирует отправку, локальное хранение и цепочки переписки."""

    MAX_ATTACHMENTS = 10
    MAX_ATTACHMENT_BYTES = 35 * 1024 * 1024

    def __init__(
        self,
        config_manager: ConfigManager,
        resend_client: ResendApiClient,
        email_repository: EmailRepository,
        sync_service: SyncService,
        read_state_repository: ReadStateRepository,
        email_flags_repository: EmailFlagsRepository,
    ) -> None:
        self._config = config_manager
        self._client = resend_client
        self._emails = email_repository
        self._sync = sync_service
        self._reads = read_state_repository
        self._flags = email_flags_repository
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
    def _require_content(
        html: str,
        text: str,
        attachments: list[AttachmentDto],
        error_message: str,
    ) -> None:
        if not html.strip() and not text.strip() and not attachments:
            raise HTTPException(status_code=400, detail=error_message)

    def _build_attachments(self, attachments: list[AttachmentDto]) -> list[dict[str, Any]]:
        if not attachments:
            return []
        if len(attachments) > self.MAX_ATTACHMENTS:
            raise HTTPException(
                status_code=400,
                detail=f"Не более {self.MAX_ATTACHMENTS} файлов за раз",
            )

        payload: list[dict[str, Any]] = []
        total_bytes = 0
        for item in attachments:
            filename = item.filename.strip()
            if not filename:
                raise HTTPException(status_code=400, detail="Имя файла не может быть пустым")

            content = item.content.strip()
            if content.startswith("data:") and "," in content:
                content = content.split(",", 1)[1]

            approx_size = (len(content) * 3) // 4
            total_bytes += approx_size
            if total_bytes > self.MAX_ATTACHMENT_BYTES:
                raise HTTPException(status_code=400, detail="Общий размер вложений больше 35 МБ")

            att: dict[str, Any] = {"filename": filename, "content": content}
            if item.content_type.strip():
                att["content_type"] = item.content_type.strip()
            payload.append(att)
        return payload

    def sync_mailbox(self) -> dict[str, Any]:
        """Полная синхронизация с Resend (ручной запуск)."""
        return self._sync.sync_all()

    def _emails_from_db(self) -> tuple[list[dict], list[dict]]:
        """Читает последние письма из локальной БД."""
        return self._emails.list_received(), self._emails.list_sent()

    def _enrich_thread_from_db_or_api(self, thread: Thread) -> None:
        """Дополняет тело письма из БД или Resend API (только для открытой цепочки)."""
        for msg in thread.messages:
            stored = self._emails.get_by_id(msg.id)
            if stored:
                msg.html = stored.get("html")
                msg.text = stored.get("text")
                if stored.get("message_id"):
                    msg.message_id = stored.get("message_id")
                if stored.get("last_event"):
                    msg.last_event = stored.get("last_event")
                if msg.html or msg.text:
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

    def _list_message_attachments(self, email_id: str, source: str) -> list[dict[str, Any]]:
        try:
            result = self._client.list_attachments(email_id, source)
            items = result.get("data") if isinstance(result, dict) else result
            if not isinstance(items, list):
                return []
            return [
                {
                    "id": item.get("id"),
                    "filename": item.get("filename") or "file",
                    "content_type": item.get("content_type"),
                    "size": item.get("size"),
                }
                for item in items
                if item.get("id")
            ]
        except HTTPException:
            return []

    def _attach_metadata_to_detail(self, detail: dict[str, Any]) -> dict[str, Any]:
        messages = detail.get("messages") or []
        for msg in messages:
            source = msg.get("source") or ("received" if msg.get("direction") == "inbound" else "sent")
            msg["attachments"] = self._list_message_attachments(msg.get("id", ""), source)
        return detail

    def _find_thread_fast(self, mailbox: Mailbox, thread_id: str) -> Thread | None:
        received, sent = self._emails_from_db()
        threads = self._threads.build_threads(mailbox, received, sent, include_details=False)
        return next((t for t in threads if t.id == thread_id), None)

    @staticmethod
    def _filter_deleted_messages(thread: Thread, email_flags: dict[str, dict[str, bool]]) -> bool:
        thread.messages = [
            m for m in thread.messages
            if not email_flags.get(m.id, {}).get("is_deleted")
        ]
        return bool(thread.messages)

    @staticmethod
    def _thread_is_starred(
        thread: Thread,
        email_flags: dict[str, dict[str, bool]],
        thread_stars: dict[str, bool],
    ) -> bool:
        if thread_stars.get(thread.id):
            return True
        return any(email_flags.get(m.id, {}).get("is_starred") for m in thread.messages)

    @staticmethod
    def _message_star_map(
        thread: Thread,
        email_flags: dict[str, dict[str, bool]],
    ) -> dict[str, bool]:
        return {
            m.id: bool(email_flags.get(m.id, {}).get("is_starred"))
            for m in thread.messages
        }

    def _email_in_mailbox(self, mailbox: Mailbox, email_id: str) -> bool:
        received, sent = self._emails_from_db()
        threads = self._threads.build_threads(mailbox, received, sent, include_details=False)
        return any(m.id == email_id for t in threads for m in t.messages)

    def _prepare_threads(
        self,
        threads: list[Thread],
        user_id: str,
        mailbox_id: str,
    ) -> list[dict[str, Any]]:
        read_map = self._reads.list_for_mailbox(user_id, mailbox_id)
        email_flags = self._flags.list_email_flags(user_id)
        thread_stars = self._flags.list_thread_stars(user_id, mailbox_id)
        summaries: list[dict[str, Any]] = []
        for thread in threads:
            if not self._filter_deleted_messages(thread, email_flags):
                continue
            starred = self._thread_is_starred(thread, email_flags, thread_stars)
            summaries.append(thread.to_summary(read_map.get(thread.id), is_starred=starred))
        summaries.sort(key=lambda s: s.get("last_message_at") or "", reverse=True)
        starred_list = [s for s in summaries if s.get("is_starred")]
        regular = [s for s in summaries if not s.get("is_starred")]
        return starred_list + regular

    def list_threads(self, mailbox_id: str, user_id: str, sync: bool = False) -> dict[str, Any]:
        """Список цепочек из SQLite; sync=True — быстрая догрузка новых с Resend."""
        mailbox = self._require_mailbox(mailbox_id)
        if sync:
            sync_info = self._sync.sync_incremental()
        else:
            sync_info = {"skipped": True, "from_cache": True}
        received, sent = self._emails_from_db()
        threads = self._threads.build_threads(mailbox, received, sent, include_details=False)
        summaries = self._prepare_threads(threads, user_id, mailbox_id)
        unread_total = sum(1 for s in summaries if s.get("is_unread"))
        return {
            "mailbox_id": mailbox_id,
            "threads": summaries,
            "total": len(summaries),
            "unread_total": unread_total,
            "sync": sync_info,
        }

    def get_thread(self, mailbox_id: str, thread_id: str, user_id: str) -> dict[str, Any]:
        """Полная цепочка из SQLite."""
        mailbox = self._require_mailbox(mailbox_id)
        thread = self._find_thread_fast(mailbox, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Цепочка не найдена")

        email_flags = self._flags.list_email_flags(user_id)
        thread_stars = self._flags.list_thread_stars(user_id, mailbox_id)
        if not self._filter_deleted_messages(thread, email_flags):
            raise HTTPException(status_code=404, detail="Цепочка не найдена")

        self._enrich_thread_from_db_or_api(thread)
        read_at = self._reads.get_read_at(user_id, mailbox_id, thread_id)
        starred = self._thread_is_starred(thread, email_flags, thread_stars)
        detail = thread.to_detail(
            read_at,
            is_starred=starred,
            message_stars=self._message_star_map(thread, email_flags),
        )
        return self._attach_metadata_to_detail(detail)

    def mark_thread_read(self, mailbox_id: str, thread_id: str, user_id: str) -> dict[str, Any]:
        """Отмечает цепочку прочитанной для пользователя."""
        mailbox = self._require_mailbox(mailbox_id)
        thread = self._find_thread_fast(mailbox, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Цепочка не найдена")
        read_at = thread.last_message_at or datetime.now(timezone.utc).isoformat()
        self._reads.mark_read(user_id, mailbox_id, thread_id, read_at)
        return {"ok": True, "thread_id": thread_id, "read_at": read_at}

    def mark_all_threads_read(self, mailbox_id: str, user_id: str) -> dict[str, Any]:
        """Отмечает все цепочки ящика прочитанными."""
        mailbox = self._require_mailbox(mailbox_id)
        received, sent = self._emails_from_db()
        threads = self._threads.build_threads(mailbox, received, sent, include_details=False)
        to_mark = {t.id: t.last_message_at for t in threads if t.last_message_at}
        self._reads.mark_many(user_id, mailbox_id, to_mark)
        return {"ok": True, "marked": len(to_mark)}

    def unread_counts_for_user(self, user) -> dict[str, int]:
        """Непрочитанные цепочки по доступным пользователю ящикам."""
        boxes = self._config.list_mailboxes_for_user(user)
        return self.unread_counts(user.id, [b.id for b in boxes])

    def unread_counts(self, user_id: str, mailbox_ids: list[str]) -> dict[str, int]:
        """Количество непрочитанных цепочек по каждому ящику."""
        if not mailbox_ids:
            return {}
        received, sent = self._emails_from_db()
        counts: dict[str, int] = {}
        for mailbox_id in mailbox_ids:
            try:
                mailbox = self._config.require_mailbox(mailbox_id)
            except ValueError:
                continue
            threads = self._threads.build_threads(mailbox, received, sent, include_details=False)
            summaries = self._prepare_threads(threads, user_id, mailbox_id)
            counts[mailbox_id] = sum(1 for s in summaries if s.get("is_unread"))
        return counts

    def star_thread(
        self,
        mailbox_id: str,
        thread_id: str,
        user_id: str,
        starred: bool,
    ) -> dict[str, Any]:
        mailbox = self._require_mailbox(mailbox_id)
        thread = self._find_thread_fast(mailbox, thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Цепочка не найдена")
        self._flags.set_thread_starred(user_id, mailbox_id, thread_id, starred)
        return {"ok": True, "thread_id": thread_id, "starred": starred}

    def star_email(
        self,
        mailbox_id: str,
        email_id: str,
        user_id: str,
        starred: bool,
    ) -> dict[str, Any]:
        mailbox = self._require_mailbox(mailbox_id)
        if not self._email_in_mailbox(mailbox, email_id):
            raise HTTPException(status_code=404, detail="Письмо не найдено")
        self._flags.set_email_starred(user_id, email_id, starred)
        return {"ok": True, "email_id": email_id, "starred": starred}

    def delete_email(
        self,
        mailbox_id: str,
        email_id: str,
        user_id: str,
    ) -> dict[str, Any]:
        mailbox = self._require_mailbox(mailbox_id)
        if not self._email_in_mailbox(mailbox, email_id):
            raise HTTPException(status_code=404, detail="Письмо не найдено")
        self._flags.set_email_deleted(user_id, email_id, True)
        return {"ok": True, "email_id": email_id, "deleted": True}

    def get_attachment_download(
        self,
        mailbox_id: str,
        email_id: str,
        attachment_id: str,
    ) -> dict[str, Any]:
        mailbox = self._require_mailbox(mailbox_id)
        if not self._email_in_mailbox(mailbox, email_id):
            raise HTTPException(status_code=404, detail="Письмо не найдено")

        stored = self._emails.get_by_id(email_id)
        if not stored:
            raise HTTPException(status_code=404, detail="Письмо не найдено")

        source = stored.get("source", "sent")
        meta = self._client.get_attachment(email_id, attachment_id, source)
        download_url = meta.get("download_url") if isinstance(meta, dict) else None
        if not download_url:
            raise HTTPException(status_code=404, detail="Ссылка на файл недоступна")
        return {
            "download_url": download_url,
            "filename": meta.get("filename") or "file",
        }

    def send_email(self, dto: SendEmailDto) -> dict[str, Any]:
        mailbox = self._require_mailbox(dto.mailbox_id)
        to_list = self._parser.parse(dto.to)
        if not to_list:
            raise HTTPException(status_code=400, detail="Укажите получателя.")
        attachments = self._build_attachments(dto.attachments)
        self._require_content(
            dto.html,
            dto.text,
            dto.attachments,
            "Укажите текст письма или прикрепите файл.",
        )

        params: dict[str, Any] = {
            "from": mailbox.from_address(),
            "to": to_list,
            "subject": dto.subject.strip(),
        }
        if dto.html.strip():
            params["html"] = dto.html
        if dto.text.strip():
            params["text"] = dto.text
        if attachments:
            params["attachments"] = attachments

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
        attachments = self._build_attachments(dto.attachments)
        self._require_content(
            dto.html,
            dto.text,
            dto.attachments,
            "Укажите текст ответа или прикрепите файл.",
        )

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
        if attachments:
            params["attachments"] = attachments

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
