"""Флаги писем и цепочек (избранное, удаление) — отдельно для каждого пользователя."""

from datetime import datetime, timezone

from app.db.database import DatabaseManager


class EmailFlagsRepository:
    """Избранное и скрытие писем/цепочек для пользователя."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def list_email_flags(self, user_id: str) -> dict[str, dict[str, bool]]:
        with self._db.connection() as conn:
            rows = conn.execute(
                """
                SELECT email_id, is_starred, is_deleted FROM email_user_flags
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchall()
            return {
                r["email_id"]: {
                    "is_starred": bool(r["is_starred"]),
                    "is_deleted": bool(r["is_deleted"]),
                }
                for r in rows
            }

    def list_thread_stars(self, user_id: str, mailbox_id: str) -> dict[str, bool]:
        with self._db.connection() as conn:
            rows = conn.execute(
                """
                SELECT thread_id, is_starred FROM thread_stars
                WHERE user_id = ? AND mailbox_id = ?
                """,
                (user_id, mailbox_id),
            ).fetchall()
            return {r["thread_id"]: bool(r["is_starred"]) for r in rows}

    def set_email_starred(self, user_id: str, email_id: str, starred: bool) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO email_user_flags (user_id, email_id, is_starred, is_deleted, updated_at)
                VALUES (?, ?, ?, 0, ?)
                ON CONFLICT(user_id, email_id) DO UPDATE SET
                    is_starred = excluded.is_starred,
                    updated_at = excluded.updated_at
                """,
                (user_id, email_id, int(starred), self._now()),
            )
            conn.commit()

    def set_email_deleted(self, user_id: str, email_id: str, deleted: bool = True) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO email_user_flags (user_id, email_id, is_starred, is_deleted, updated_at)
                VALUES (?, ?, 0, ?, ?)
                ON CONFLICT(user_id, email_id) DO UPDATE SET
                    is_deleted = excluded.is_deleted,
                    updated_at = excluded.updated_at
                """,
                (user_id, email_id, int(deleted), self._now()),
            )
            conn.commit()

    def set_thread_starred(
        self,
        user_id: str,
        mailbox_id: str,
        thread_id: str,
        starred: bool,
    ) -> None:
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO thread_stars (user_id, mailbox_id, thread_id, is_starred, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, mailbox_id, thread_id) DO UPDATE SET
                    is_starred = excluded.is_starred,
                    updated_at = excluded.updated_at
                """,
                (user_id, mailbox_id, thread_id, int(starred), self._now()),
            )
            conn.commit()
