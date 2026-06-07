"""Репозиторий пользователей и их доступа к ящикам."""

import uuid
from datetime import datetime, timezone

from app.db.database import DatabaseManager
from app.models.user import User


class UserRepository:
    """CRUD пользователей и связей user ↔ mailbox."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def count(self) -> int:
        with self._db.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
            return int(row["c"])

    def _load_mailbox_ids(self, conn, user_id: str) -> list[str]:
        rows = conn.execute(
            "SELECT mailbox_id FROM user_mailboxes WHERE user_id = ? ORDER BY mailbox_id",
            (user_id,),
        ).fetchall()
        return [r["mailbox_id"] for r in rows]

    def _row_to_user(self, conn, row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            is_admin=bool(row["is_admin"]),
            is_active=bool(row["is_active"]),
            mailbox_ids=self._load_mailbox_ids(conn, row["id"]),
        )

    def get_by_id(self, user_id: str) -> User | None:
        with self._db.connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return self._row_to_user(conn, row) if row else None

    def get_by_username(self, username: str) -> User | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
                (username.strip(),),
            ).fetchone()
            return self._row_to_user(conn, row) if row else None

    def get_password_hash(self, user_id: str) -> str | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            return row["password_hash"] if row else None

    def list_all(self) -> list[User]:
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY created_at ASC"
            ).fetchall()
            return [self._row_to_user(conn, r) for r in rows]

    def create(
        self,
        username: str,
        password_hash: str,
        *,
        is_admin: bool = False,
        mailbox_ids: list[str] | None = None,
    ) -> User:
        username = username.strip()
        if self.get_by_username(username):
            raise ValueError(f"Пользователь «{username}» уже существует")

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO users (id, username, password_hash, is_admin, is_active, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (user_id, username, password_hash, int(is_admin), now),
            )
            self._replace_mailbox_ids(conn, user_id, mailbox_ids or [])
            conn.commit()
        return self.get_by_id(user_id)  # type: ignore[return-value]

    def update(
        self,
        user_id: str,
        *,
        password_hash: str | None = None,
        is_admin: bool | None = None,
        is_active: bool | None = None,
        mailbox_ids: list[str] | None = None,
    ) -> User:
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        fields: list[str] = []
        values: list[object] = []
        if password_hash is not None:
            fields.append("password_hash = ?")
            values.append(password_hash)
        if is_admin is not None:
            fields.append("is_admin = ?")
            values.append(int(is_admin))
        if is_active is not None:
            fields.append("is_active = ?")
            values.append(int(is_active))

        with self._db.connection() as conn:
            if fields:
                values.append(user_id)
                conn.execute(
                    f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
                    values,
                )
            if mailbox_ids is not None:
                self._replace_mailbox_ids(conn, user_id, mailbox_ids)
            conn.commit()
        return self.get_by_id(user_id)  # type: ignore[return-value]

    def delete(self, user_id: str) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

    @staticmethod
    def _replace_mailbox_ids(conn, user_id: str, mailbox_ids: list[str]) -> None:
        conn.execute("DELETE FROM user_mailboxes WHERE user_id = ?", (user_id,))
        for mailbox_id in mailbox_ids:
            conn.execute(
                "INSERT OR IGNORE INTO user_mailboxes (user_id, mailbox_id) VALUES (?, ?)",
                (user_id, mailbox_id),
            )
