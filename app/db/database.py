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
