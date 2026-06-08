"""Менеджер подключения и схемы SQLite."""

import sqlite3
from pathlib import Path


class DatabaseManager:
    """Создаёт БД, применяет схему и выдаёт соединения."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS app_settings (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS mailboxes (
        id         TEXT PRIMARY KEY,
        name       TEXT NOT NULL DEFAULT '',
        email      TEXT NOT NULL UNIQUE,
        color      TEXT NOT NULL DEFAULT '#6366f1',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS emails (
        id           TEXT PRIMARY KEY,
        source       TEXT NOT NULL,
        direction    TEXT NOT NULL,
        from_addr    TEXT NOT NULL DEFAULT '',
        to_addrs     TEXT NOT NULL DEFAULT '[]',
        cc_addrs     TEXT NOT NULL DEFAULT '[]',
        bcc_addrs    TEXT NOT NULL DEFAULT '[]',
        reply_to     TEXT NOT NULL DEFAULT '[]',
        subject      TEXT NOT NULL DEFAULT '',
        html         TEXT,
        text_content TEXT,
        message_id   TEXT,
        last_event   TEXT,
        created_at   TEXT NOT NULL,
        synced_at    TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_emails_created ON emails(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_emails_source ON emails(source);

    CREATE TABLE IF NOT EXISTS users (
        id            TEXT PRIMARY KEY,
        username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        is_admin      INTEGER NOT NULL DEFAULT 0,
        is_active     INTEGER NOT NULL DEFAULT 1,
        created_at    TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS user_mailboxes (
        user_id    TEXT NOT NULL,
        mailbox_id TEXT NOT NULL,
        PRIMARY KEY (user_id, mailbox_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (mailbox_id) REFERENCES mailboxes(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS sessions (
        token      TEXT PRIMARY KEY,
        user_id    TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

    CREATE TABLE IF NOT EXISTS thread_reads (
        user_id    TEXT NOT NULL,
        mailbox_id TEXT NOT NULL,
        thread_id  TEXT NOT NULL,
        read_at    TEXT NOT NULL,
        PRIMARY KEY (user_id, mailbox_id, thread_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_thread_reads_mailbox
        ON thread_reads(user_id, mailbox_id);

    CREATE TABLE IF NOT EXISTS email_user_flags (
        user_id    TEXT NOT NULL,
        email_id   TEXT NOT NULL,
        is_starred INTEGER NOT NULL DEFAULT 0,
        is_deleted INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (user_id, email_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS thread_stars (
        user_id    TEXT NOT NULL,
        mailbox_id TEXT NOT NULL,
        thread_id  TEXT NOT NULL,
        is_starred INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (user_id, mailbox_id, thread_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_thread_stars_mailbox
        ON thread_stars(user_id, mailbox_id);
    """

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent.parent / "data" / "resend_gui.db"
        self._path = db_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @property
    def path(self) -> Path:
        """Путь к файлу базы данных."""
        return self._path

    def _init_schema(self) -> None:
        """Применяет SQL-схему при первом запуске."""
        with self.connection() as conn:
            conn.executescript(self.SCHEMA)

    def connection(self) -> sqlite3.Connection:
        """Открывает соединение с row_factory=Row."""
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
