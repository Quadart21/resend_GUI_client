"""Синхронизация писем Resend → SQLite."""

from typing import Any

from fastapi import HTTPException

from app.repositories.email_repository import EmailRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.resend_client import ResendApiClient


class SyncService:
    """Загружает письма из Resend API и сохраняет в локальную БД."""

    def __init__(
        self,
        client: ResendApiClient,
        emails: EmailRepository,
        settings: SettingsRepository,
        max_pages: int = 10,
    ) -> None:
        self._client = client
        self._emails = emails
        self._settings = settings
        self._max_pages = max_pages

    def _can_sync(self) -> bool:
        return self._settings.has_api_key()

    def _paginate(self, fetch_page) -> list[dict]:
        """Обходит страницы списка Resend."""
        items: list[dict] = []
        after: str | None = None
        for _ in range(self._max_pages):
            result = fetch_page(after)
            batch = result.get("data") or []
            items.extend(batch)
            if not result.get("has_more") or not batch:
                break
            after = batch[-1]["id"]
        return items

    def _sync_source(self, source: str, fetch_list, fetch_one) -> int:
        """Синхронизирует входящие или исходящие."""
        items = self._paginate(fetch_list)
        synced = 0
        for item in items:
            email_id = item.get("id")
            if not email_id:
                continue
            stored = self._emails.get_by_id(email_id)
            needs_body = not stored or (not stored.get("html") and not stored.get("text"))
            if needs_body:
                try:
                    full = fetch_one(email_id)
                    self._emails.upsert_from_api(full, source)
                except HTTPException:
                    self._emails.upsert_list_item(item, source)
            else:
                self._emails.upsert_list_item(item, source)
            synced += 1
        return synced

    def sync_all(self) -> dict[str, Any]:
        """
        Полная синхронизация с Resend.

        :returns: статистика или ``skipped`` если нет API-ключа
        """
        if not self._can_sync():
            return {"skipped": True, "reason": "API ключ не задан"}

        try:
            self._client._activate()
        except HTTPException as exc:
            return {"skipped": True, "reason": str(exc.detail)}

        received = self._sync_source(
            "received",
            self._client.list_received,
            self._client.get_received,
        )
        sent = self._sync_source(
            "sent",
            self._client.list_sent,
            self._client.get_sent,
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
