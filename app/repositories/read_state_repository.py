"""Состояние «прочитано» для цепочек (отдельно для каждого пользователя)."""

from datetime import datetime, timezone

from app.db.database import DatabaseManager


class ReadStateRepository:
    """Хранит момент последнего прочтения цепочки пользователем."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_read_at(self, user_id: str, mailbox_id: str, thread_id: str) -> str | None:
        with self._db.connection() as conn:
            row = conn.execute(
                """
                SELECT read_at FROM thread_reads
                WHERE user_id = ? AND mailbox_id = ? AND thread_id = ?
                """,
                (user_id, mailbox_id, thread_id),
            ).fetchone()
            return row["read_at"] if row else None

    def list_for_mailbox(self, user_id: str, mailbox_id: str) -> dict[str, str]:
        with self._db.connection() as conn:
            rows = conn.execute(
                """
                SELECT thread_id, read_at FROM thread_reads
                WHERE user_id = ? AND mailbox_id = ?
                """,
                (user_id, mailbox_id),
            ).fetchall()
            return {r["thread_id"]: r["read_at"] for r in rows}

    def mark_read(
        self,
        user_id: str,
        mailbox_id: str,
        thread_id: str,
        read_at: str | None = None,
    ) -> None:
        ts = read_at or self._now()
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO thread_reads (user_id, mailbox_id, thread_id, read_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, mailbox_id, thread_id) DO UPDATE SET
                    read_at = excluded.read_at
                """,
                (user_id, mailbox_id, thread_id, ts),
            )
            conn.commit()

    def mark_many(
        self,
        user_id: str,
        mailbox_id: str,
        thread_reads: dict[str, str],
    ) -> None:
        if not thread_reads:
            return
        with self._db.connection() as conn:
            for thread_id, read_at in thread_reads.items():
                conn.execute(
                    """
                    INSERT INTO thread_reads (user_id, mailbox_id, thread_id, read_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, mailbox_id, thread_id) DO UPDATE SET
                        read_at = excluded.read_at
                    """,
                    (user_id, mailbox_id, thread_id, read_at),
                )
            conn.commit()
