"""Репозиторий почтовых ящиков."""

import uuid
from datetime import datetime, timezone

from app.db.database import DatabaseManager
from app.models.mailbox import MAILBOX_COLORS, Mailbox


class MailboxRepository:
    """CRUD для таблицы mailboxes."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    @staticmethod
    def _row_to_mailbox(row) -> Mailbox:
        return Mailbox(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            color=row["color"],
        )

    def list_all(self) -> list[Mailbox]:
        """Возвращает все ящики."""
        with self._db.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM mailboxes ORDER BY created_at ASC"
            ).fetchall()
            return [self._row_to_mailbox(r) for r in rows]

    def get_by_id(self, mailbox_id: str) -> Mailbox | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE id = ?", (mailbox_id,)
            ).fetchone()
            return self._row_to_mailbox(row) if row else None

    def get_by_email(self, email: str) -> Mailbox | None:
        with self._db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?", (email.lower(),)
            ).fetchone()
            return self._row_to_mailbox(row) if row else None

    def create(self, name: str, email: str) -> Mailbox:
        """Создаёт новый ящик."""
        email = email.strip().lower()
        if self.get_by_email(email):
            raise ValueError(f"Ящик {email} уже существует")

        count = len(self.list_all())
        box = Mailbox(
            id=str(uuid.uuid4()),
            name=name.strip(),
            email=email,
            color=MAILBOX_COLORS[count % len(MAILBOX_COLORS)],
        )
        now = datetime.now(timezone.utc).isoformat()
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO mailboxes (id, name, email, color, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (box.id, box.name, box.email, box.color, now),
            )
            conn.commit()
        return box

    def update(self, mailbox_id: str, name: str, email: str) -> Mailbox:
        email = email.strip().lower()
        existing = self.get_by_email(email)
        if existing and existing.id != mailbox_id:
            raise ValueError(f"Ящик {email} уже существует")

        box = self.get_by_id(mailbox_id)
        if not box:
            raise ValueError(f"Ящик {mailbox_id} не найден")

        with self._db.connection() as conn:
            conn.execute(
                "UPDATE mailboxes SET name = ?, email = ? WHERE id = ?",
                (name.strip(), email, mailbox_id),
            )
            conn.commit()
        box.name = name.strip()
        box.email = email
        return box

    def delete(self, mailbox_id: str) -> None:
        with self._db.connection() as conn:
            conn.execute("DELETE FROM mailboxes WHERE id = ?", (mailbox_id,))
            conn.commit()

    def upsert_from_dict(self, data: dict) -> Mailbox:
        """Импорт ящика при миграции из config.json."""
        box = Mailbox.from_dict(data)
        now = datetime.now(timezone.utc).isoformat()
        with self._db.connection() as conn:
            conn.execute(
                """
                INSERT INTO mailboxes (id, name, email, color, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(email) DO UPDATE SET
                    name = excluded.name,
                    color = excluded.color
                """,
                (box.id, box.name, box.email, box.color, now),
            )
            conn.commit()
        return self.get_by_email(box.email) or box
