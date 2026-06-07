"""Проверка подписи webhook Resend (Svix)."""

import json
import os

from fastapi import HTTPException

from app.repositories.settings_repository import SettingsRepository

try:
    from svix.webhooks import Webhook, WebhookVerificationError
except ImportError:  # pragma: no cover
    Webhook = None  # type: ignore[misc, assignment]
    WebhookVerificationError = Exception  # type: ignore[misc, assignment]


class WebhookVerifierService:
    """Проверяет заголовки svix-* и signing secret от Resend."""

    def __init__(self, settings_repo: SettingsRepository) -> None:
        self._settings = settings_repo

    def get_secret(self) -> str:
        """Секрет из env или SQLite (env имеет приоритет)."""
        env = os.getenv("RESEND_WEBHOOK_SECRET", "").strip()
        if env:
            return env
        return self._settings.get("webhook_secret", "").strip()

    def is_configured(self) -> bool:
        return bool(self.get_secret())

    def verify(self, body: bytes, headers) -> dict:
        """
        Проверяет подпись и возвращает распарсенный JSON.

        Если секрет не задан — принимает запрос (режим совместимости).
        """
        secret = self.get_secret()
        if not secret:
            try:
                return json.loads(body.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail="Некорректный JSON") from exc

        if Webhook is None:
            raise HTTPException(
                status_code=500,
                detail="Пакет svix не установлен",
            )

        svix_headers = {
            "svix-id": headers.get("svix-id"),
            "svix-timestamp": headers.get("svix-timestamp"),
            "svix-signature": headers.get("svix-signature"),
        }
        if not all(svix_headers.values()):
            raise HTTPException(
                status_code=400,
                detail="Отсутствуют заголовки svix-id / svix-timestamp / svix-signature",
            )

        try:
            wh = Webhook(secret)
            verified = wh.verify(body, svix_headers)
        except WebhookVerificationError as exc:
            raise HTTPException(status_code=401, detail="Неверная подпись webhook") from exc

        if isinstance(verified, dict):
            return verified
        if isinstance(verified, (str, bytes)):
            return json.loads(verified)
        return json.loads(body.decode("utf-8"))
