"""Синхронизация писем Resend → SQLite."""

from typing import Any, Callable

from fastapi import HTTPException

from app.repositories.email_repository import EmailRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.resend_client import ResendApiClient


class SyncService:
    """Загружает письма из Resend API и сохраняет в локальную БД."""

    INCREMENTAL_PAGES = 2
    FULL_SYNC_PAGES = 10

    def __init__(
        self,
        client: ResendApiClient,
        emails: EmailRepository,
        settings: SettingsRepository,
    ) -> None:
        self._client = client
        self._emails = emails
        self._settings = settings

    def _can_sync(self) -> bool:
        return self._settings.has_api_key()

    def _paginate(
        self,
        fetch_page: Callable[[str | None], dict],
        max_pages: int,
        *,
        stop_when_known: bool = False,
    ) -> list[dict]:
        """Обходит страницы списка Resend (только метаданные, без тел писем)."""
        items: list[dict] = []
        after: str | None = None

        for _ in range(max_pages):
            result = fetch_page(after)
            batch = result.get("data") or []
            if not batch:
                break

            items.extend(batch)

            if stop_when_known:
                ids = [i.get("id") for i in batch if i.get("id")]
                if ids and all(self._emails.exists(email_id) for email_id in ids):
                    break

            if not result.get("has_more"):
                break
            after = batch[-1]["id"]

        return items

    def _sync_source(self, source: str, fetch_list: Callable, max_pages: int, *, stop_when_known: bool) -> int:
        """
        Синхронизирует входящие или исходящие — только списком API.

        Тела писем подгружаются при открытии переписки или через webhook.
        """
        items = self._paginate(fetch_list, max_pages, stop_when_known=stop_when_known)
        synced = 0
        for item in items:
            email_id = item.get("id")
            if not email_id:
                continue
            self._emails.upsert_list_item(item, source)
            synced += 1
        return synced

    def _run_sync(self, max_pages: int, *, stop_when_known: bool) -> dict[str, Any]:
        if not self._can_sync():
            return {"skipped": True, "reason": "API ключ не задан"}

        try:
            self._client._activate()
        except HTTPException as exc:
            return {"skipped": True, "reason": str(exc.detail)}

        received = self._sync_source(
            "received",
            self._client.list_received,
            max_pages,
            stop_when_known=stop_when_known,
        )
        sent = self._sync_source(
            "sent",
            self._client.list_sent,
            max_pages,
            stop_when_known=stop_when_known,
        )
        total = self._emails.count()
        self._settings.set("emails_count", str(total))
        self._settings.set("last_sync_at", self._emails._now())

        return {
            "ok": True,
            "received_synced": received,
            "sent_synced": sent,
            "total_stored": total,
        }

    def sync_incremental(self) -> dict[str, Any]:
        """Быстрая синхронизация: 1–2 страницы, остановка на уже известных письмах."""
        return self._run_sync(
            self.INCREMENTAL_PAGES,
            stop_when_known=True,
        )

    def sync_all(self) -> dict[str, Any]:
        """Полная синхронизация (кнопка админа / ручной sync)."""
        return self._run_sync(
            self.FULL_SYNC_PAGES,
            stop_when_known=False,
        )

    def store_received_by_id(self, email_id: str) -> None:
        """Сохраняет одно входящее письмо по ID (webhook)."""
        if not self._can_sync():
            return
        self._client._activate()
        full = self._client.get_received(email_id)
        self._emails.upsert_from_api(full, "received")
        self._settings.set("emails_count", str(self._emails.count()))

    def store_sent_by_id(self, email_id: str) -> None:
        """Сохраняет одно исходящее письмо по ID."""
        if not self._can_sync():
            return
        self._client._activate()
        full = self._client.get_sent(email_id)
        self._emails.upsert_from_api(full, "sent")
        self._settings.set("emails_count", str(self._emails.count()))
