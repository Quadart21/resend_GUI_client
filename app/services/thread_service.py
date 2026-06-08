"""Сервис группировки писем в цепочки переписки."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models.mailbox import Mailbox
from app.utils.email_helper import EmailHelper


@dataclass
class ThreadMessage:
    """Одно сообщение внутри цепочки."""

    id: str
    direction: str  # inbound | outbound
    source: str  # received | sent
    from_addr: str
    to_addrs: list[str]
    subject: str
    created_at: str
    message_id: str | None = None
    html: str | None = None
    text: str | None = None
    last_event: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Сериализация для API."""
        return {
            "id": self.id,
            "direction": self.direction,
            "source": self.source,
            "from": self.from_addr,
            "to": self.to_addrs,
            "subject": self.subject,
            "created_at": self.created_at,
            "message_id": self.message_id,
            "html": self.html,
            "text": self.text,
            "last_event": self.last_event,
            "is_unread": False,
        }

    def to_dict_with_read(self, read_at: str | None, *, is_starred: bool = False) -> dict[str, Any]:
        """Сериализация с флагами непрочитанного и избранного."""
        data = self.to_dict()
        data["is_unread"] = (
            self.direction == "inbound"
            and (not read_at or self.created_at > read_at)
        )
        data["is_starred"] = is_starred
        return data


@dataclass
class Thread:
    """Цепочка переписки (несколько писем по одной теме)."""

    id: str
    subject: str
    participants: list[str]
    messages: list[ThreadMessage] = field(default_factory=list)
    mailbox_id: str = ""

    @property
    def last_message_at(self) -> str:
        """Дата последнего сообщения в цепочке."""
        if not self.messages:
            return ""
        return max(m.created_at for m in self.messages)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def preview(self) -> str:
        """Краткий текст последнего сообщения."""
        if not self.messages:
            return ""
        last = sorted(self.messages, key=lambda m: m.created_at)[-1]
        if last.text:
            return last.text[:120]
        if last.html:
            import re
            plain = re.sub(r"<[^>]+>", "", last.html)
            return plain[:120]
        if last.subject:
            return last.subject[:120]
        return ""

    @property
    def correspondent(self) -> str:
        """Основной собеседник (не наш ящик)."""
        for msg in sorted(self.messages, key=lambda m: m.created_at, reverse=True):
            if msg.direction == "inbound":
                return EmailHelper.display_name(msg.from_addr)
            if msg.to_addrs:
                return EmailHelper.display_name(msg.to_addrs[0])
        return "—"

    @staticmethod
    def _unread_stats(messages: list[ThreadMessage], read_at: str | None) -> tuple[bool, int]:
        inbound = [m for m in messages if m.direction == "inbound"]
        if not inbound:
            return False, 0
        unread = [m for m in inbound if not read_at or m.created_at > read_at]
        return len(unread) > 0, len(unread)

    def to_summary(self, read_at: str | None = None, *, is_starred: bool = False) -> dict[str, Any]:
        """Краткое описание цепочки для списка."""
        last = sorted(self.messages, key=lambda m: m.created_at)[-1] if self.messages else None
        is_unread, unread_count = self._unread_stats(self.messages, read_at)
        return {
            "id": self.id,
            "subject": self.subject,
            "participants": self.participants,
            "correspondent": self.correspondent,
            "last_message_at": self.last_message_at,
            "message_count": self.message_count,
            "preview": self.preview,
            "mailbox_id": self.mailbox_id,
            "last_direction": last.direction if last else "inbound",
            "is_unread": is_unread,
            "unread_count": unread_count,
            "is_starred": is_starred,
        }

    def to_detail(
        self,
        read_at: str | None = None,
        *,
        is_starred: bool = False,
        message_stars: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        """Полная цепочка с сообщениями."""
        stars = message_stars or {}
        sorted_msgs = sorted(self.messages, key=lambda m: m.created_at)
        return {
            **self.to_summary(read_at, is_starred=is_starred),
            "messages": [
                m.to_dict_with_read(
                    read_at,
                    is_starred=is_starred or stars.get(m.id, False),
                )
                for m in sorted_msgs
            ],
        }


class ThreadService:
    """Фильтрует письма по ящику и объединяет их в цепочки."""

    def __init__(self) -> None:
        self._helper = EmailHelper()

    def belongs_to_mailbox(self, mailbox: Mailbox, item: dict, source: str) -> bool:
        """
        Проверяет, относится ли письмо к указанному ящику.

        Входящие — по полю ``to``, исходящие — по полю ``from``.
        """
        box_email = mailbox.email.lower()
        if source == "received":
            recipients = self._helper.normalize_addresses(item.get("to"))
            return box_email in recipients
        from_addrs = self._helper.normalize_addresses(item.get("from"))
        return box_email in from_addrs

    def build_threads(
        self,
        mailbox: Mailbox,
        received: list[dict],
        sent: list[dict],
        include_details: bool = False,
    ) -> list[Thread]:
        """
        Строит список цепочек из входящих и исходящих писем.

        :param include_details: если False — только метаданные (без html/text)
        """
        buckets: dict[str, Thread] = {}

        for item in received:
            if not self.belongs_to_mailbox(mailbox, item, "received"):
                continue
            self._add_to_bucket(buckets, mailbox, item, "received", "inbound", include_details)

        for item in sent:
            if not self.belongs_to_mailbox(mailbox, item, "sent"):
                continue
            self._add_to_bucket(buckets, mailbox, item, "sent", "outbound", include_details)

        threads = list(buckets.values())
        threads.sort(key=lambda t: t.last_message_at, reverse=True)
        return threads

    def _add_to_bucket(
        self,
        buckets: dict[str, Thread],
        mailbox: Mailbox,
        item: dict,
        source: str,
        direction: str,
        include_details: bool,
    ) -> None:
        """Добавляет письмо в соответствующую цепочку."""
        subject = item.get("subject") or "(без темы)"
        from_addr = item.get("from", "")
        to_raw = item.get("to") or []
        to_addrs = to_raw if isinstance(to_raw, list) else [to_raw]

        participants = set(self._helper.normalize_addresses(from_addr))
        participants.update(self._helper.normalize_addresses(to_addrs))
        participants.discard(mailbox.email.lower())

        key = self._helper.thread_key(subject, participants)
        if key not in buckets:
            buckets[key] = Thread(
                id=key,
                subject=subject,
                participants=sorted(participants),
                mailbox_id=mailbox.id,
            )

        msg = ThreadMessage(
            id=item.get("id", ""),
            direction=direction,
            source=source,
            from_addr=from_addr if isinstance(from_addr, str) else str(from_addr),
            to_addrs=[str(t) for t in to_addrs],
            subject=subject,
            created_at=item.get("created_at", ""),
            message_id=item.get("message_id"),
            html=item.get("html") if include_details else None,
            text=item.get("text") if include_details else None,
            last_event=item.get("last_event"),
        )
        buckets[key].messages.append(msg)

    def find_thread(
        self,
        mailbox: Mailbox,
        thread_id: str,
        received: list[dict],
        sent: list[dict],
    ) -> Thread | None:
        """Находит одну цепочку по ID с полным содержимым писем."""
        threads = self.build_threads(mailbox, received, sent, include_details=True)
        for thread in threads:
            if thread.id == thread_id:
                return thread
        return None

    def collect_message_ids(self, thread: Thread) -> list[str]:
        """Собирает message_id всех писем цепочки для заголовка References."""
        ids: list[str] = []
        for msg in sorted(thread.messages, key=lambda m: m.created_at):
            if msg.message_id and msg.message_id not in ids:
                ids.append(msg.message_id)
        return ids
