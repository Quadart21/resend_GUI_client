"""Кэш метаданных вложений писем."""

from datetime import datetime, timezone
from typing import Any

from app.db.database import DatabaseManager


class AttachmentRepository:
    """Хранит метаданные вложений локально (без содержимого файлов)."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_item(item: dict[str, Any]) -> dict[str, Any] | None:
        att_id = item.get("id")
        if not att_id:
            return None
        return {
            "id": att_id,
            "filename": item.get("filename") or "file",
            "content_type": item.get("content_type"),
            "size": item.get("size"),
        }

    def replace_for_email(self, email_id: str, items: list[dict[str, Any]]) -> None:
        """Полностью заменяет кэш вложений для письма."""
        normalized = [n for n in (self._normalize_item(i) for i in items) if n]
        with self._db.connection() as conn:
            conn.execute("DELETE FROM email_attachments WHERE email_id = ?", (email_id,))
            for att in normalized:
                conn.execute(
                    """
                    INSERT INTO email_attachments (
                        email_id, attachment_id, filename, content_type, size, synced_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        email_id,
                        att["id"],
                        att["filename"],
                        att.get("content_type"),
                        att.get("size"),
                        self._now(),
                    ),
                )
            conn.execute(
                """
                INSERT INTO email_attachment_sync (email_id, synced_at)
                VALUES (?, ?)
                ON CONFLICT(email_id) DO UPDATE SET synced_at = excluded.synced_at
                """,
                (email_id, self._now()),
            )
            conn.commit()

    def list_for_email(self, email_id: str) -> list[dict[str, Any]]:
        with self._db.connection() as conn:
            rows = conn.execute(
                """
                SELECT attachment_id, filename, content_type, size
                FROM email_attachments
                WHERE email_id = ?
                ORDER BY rowid ASC
                """,
                (email_id,),
            ).fetchall()
        return [
            {
                "id": row["attachment_id"],
                "filename": row["filename"],
                "content_type": row["content_type"],
                "size": row["size"],
            }
            for row in rows
        ]

    def list_for_emails(self, email_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        if not email_ids:
            return {}
        placeholders = ",".join("?" * len(email_ids))
        with self._db.connection() as conn:
            rows = conn.execute(
                f"""
                SELECT email_id, attachment_id, filename, content_type, size
                FROM email_attachments
                WHERE email_id IN ({placeholders})
                ORDER BY email_id, rowid ASC
                """,
                email_ids,
            ).fetchall()
        result: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            result.setdefault(row["email_id"], []).append(
                {
                    "id": row["attachment_id"],
                    "filename": row["filename"],
                    "content_type": row["content_type"],
                    "size": row["size"],
                }
            )
        return result

    def has_cache(self, email_id: str) -> bool:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM email_attachment_sync WHERE email_id = ? LIMIT 1",
                (email_id,),
            ).fetchone()
            return row is not None
