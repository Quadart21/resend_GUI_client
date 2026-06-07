"""Репозиторий сессий авторизации."""

import secrets
from datetime import datetime, timedelta, timezone

from app.db.database import DatabaseManager


class SessionRepository:
    """Хранение токенов сессий в SQLite."""

    def __init__(self, db: DatabaseManager, ttl_days: int = 30) -> None:
        self._db = db
        self._ttl_days = ttl_days

    def create(self, user_id: str) -> str:
        """Создаёт сессию и возвращает токен."""
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self._ttl_days)
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (token, user_id, expires_at, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (token, user_id, expires.isoformat(), now.isoformat()),
            )
            conn.commit()
        return token

    def get_user_id(self, token: str) -> str | None:
        """Возвращает user_id по токену или None, если сессия просрочена."""
        if not token:
            return None
        now = datetime.now(timezone.utc).isoformat()
        with self._db.connection() as conn:
            row = conn.execute(
                """
                SELECT user_id FROM sessions
                WHERE token = ? AND expires_at > ?
                """,
                (token, now),
            ).fetchone()
            return row["user_id"] if row else None

    def delete(self, token: str) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

    def delete_for_user(self, user_id: str) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.commit()

    def purge_expired(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._db.connection() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
            conn.commit()
