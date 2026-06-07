"""Репозиторий писем (входящие и исходящие)."""

import json
from datetime import datetime, timezone
from typing import Any

from app.db.database import DatabaseManager


class EmailRepository:
    """Сохраняет и читает письма из SQLite."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _json_list(value: Any) -> str:
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        if value:
            return json.dumps([value], ensure_ascii=False)
        return "[]"

    @staticmethod
    def _parse_list(raw: str | None) -> list:
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            return []

    def _row_to_api_dict(self, row) -> dict[str, Any]:
        """Преобразует строку БД в формат, совместимый с ThreadService."""
        return {
            "id": row["id"],
            "from": row["from_addr"],
            "to": self._parse_list(row["to_addrs"]),
            "cc": self._parse_list(row["cc_addrs"]),
            "bcc": self._parse_list(row["bcc_addrs"]),
            "reply_to": self._parse_list(row["reply_to"]),
            "subject": row["subject"],
            "html": row["html"],
            "text": row["text_content"],
            "message_id": row["message_id"],
            "last_event": row["last_event"],
            "created_at": row["created_at"],
        }

    def upsert_from_api(self, data: dict[str, Any], source: str) -> None:
        """
        Сохраняет или обновляет письмо из ответа Resend API.

        :param source: ``received`` или ``sent``
        """
        direction = "inbound" if source == "received" else "outbound"
        email_id = data.get("id")
        if not email_id:
            return

        from_val = data.get("from", "")
        if isinstance(from_val, list):
            from_val = from_val[0] if from_val else ""

        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO emails (
                    id, source, direction, from_addr, to_addrs, cc_addrs, bcc_addrs,
                    reply_to, subject, html, text_content, message_id, last_event,
                    created_at, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    from_addr = excluded.from_addr,
                    to_addrs = excluded.to_addrs,
                    cc_addrs = excluded.cc_addrs,
                    bcc_addrs = excluded.bcc_addrs,
                    reply_to = excluded.reply_to,
                    subject = excluded.subject,
                    html = COALESCE(excluded.html, emails.html),
                    text_content = COALESCE(excluded.text_content, emails.text_content),
                    message_id = COALESCE(excluded.message_id, emails.message_id),
                    last_event = COALESCE(excluded.last_event, emails.last_event),
                    synced_at = excluded.synced_at
                """,
                (
                    email_id,
                    source,
                    direction,
                    str(from_val),
                    self._json_list(data.get("to")),
                    self._json_list(data.get("cc")),
                    self._json_list(data.get("bcc")),
                    self._json_list(data.get("reply_to")),
                    data.get("subject") or "",
                    data.get("html"),
                    data.get("text"),
                    data.get("message_id"),
                    data.get("last_event"),
                    data.get("created_at") or self._now(),
                    self._now(),
                ),
            )
            conn.commit()

    def upsert_list_item(self, data: dict[str, Any], source: str) -> None:
        """Обновляет метаданные из списка (без затирания html/text)."""
        existing = self.get_by_id(data.get("id", ""))
        if existing and (existing.get("html") or existing.get("text")):
            merged = {**existing, **data}
            if not data.get("html"):
                merged["html"] = existing.get("html")
            if not data.get("text"):
                merged["text"] = existing.get("text")
            self.upsert_from_api(merged, source)
        else:
            self.upsert_from_api(data, source)

    def get_by_id(self, email_id: str) -> dict[str, Any] | None:
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
            return self._row_to_api_dict(row) if row else None

    def list_by_source(self, source: str) -> list[dict[str, Any]]:
        """Все письма по типу ``received`` / ``sent``."""
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM emails WHERE source = ? ORDER BY created_at DESC",
                (source,),
            ).fetchall()
            return [self._row_to_api_dict(r) for r in rows]

    def list_received(self) -> list[dict[str, Any]]:
        return self.list_by_source("received")

    def list_sent(self) -> list[dict[str, Any]]:
        return self.list_by_source("sent")

    def count(self) -> int:
        with self._db.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM emails").fetchone()
            return int(row["c"]) if row else 0
