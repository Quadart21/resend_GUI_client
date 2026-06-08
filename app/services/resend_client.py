"""Низкоуровневый клиент Resend API."""

from typing import Any

import resend
from fastapi import HTTPException

from app.config.manager import ConfigManager


class ResendApiClient:
    """Обёртка над официальным SDK Resend с проверкой API-ключа."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager

    def _activate(self) -> None:
        """Устанавливает API-ключ в SDK или выбрасывает HTTP-ошибку."""
        settings = self._config_manager.load()
        if not settings.has_api_key():
            raise HTTPException(
                status_code=400,
                detail="API ключ не настроен. Откройте «Настройки» и укажите ключ Resend.",
            )
        resend.api_key = settings.api_key

    @staticmethod
    def _wrap_error(exc: Exception) -> HTTPException:
        """Преобразует исключение SDK в HTTP-ответ."""
        return HTTPException(status_code=502, detail=f"Ошибка Resend API: {exc}")

    def send(self, params: dict[str, Any]) -> dict:
        """Отправляет письмо через Resend."""
        self._activate()
        try:
            return resend.Emails.send(params)
        except Exception as exc:
            raise self._wrap_error(exc) from exc

    def list_sent(self, after: str | None = None) -> dict:
        """Возвращает список отправленных писем."""
        self._activate()
        try:
            if after:
                return resend.Emails.list({"after": after})
            return resend.Emails.list()
        except Exception as exc:
            raise self._wrap_error(exc) from exc

    def get_sent(self, email_id: str) -> dict:
        """Возвращает одно отправленное письмо по ID."""
        self._activate()
        try:
            return resend.Emails.get(email_id)
        except Exception as exc:
            raise self._wrap_error(exc) from exc

    def list_received(self, after: str | None = None) -> dict:
        """Возвращает список входящих писем."""
        self._activate()
        try:
            if after:
                return resend.Emails.Receiving.list({"after": after})
            return resend.Emails.Receiving.list()
        except Exception as exc:
            raise self._wrap_error(exc) from exc

    def get_received(self, email_id: str) -> dict:
        """Возвращает одно входящее письмо по ID."""
        self._activate()
        try:
            return resend.Emails.Receiving.get(email_id)
        except Exception as exc:
            raise self._wrap_error(exc) from exc

    def list_attachments(self, email_id: str, source: str) -> dict:
        """Список вложений письма (source: received | sent)."""
        self._activate()
        try:
            if source == "received":
                return resend.Emails.Receiving.Attachments.list(email_id)
            return resend.Emails.Attachments.list(email_id)
        except Exception as exc:
            raise self._wrap_error(exc) from exc

    def get_attachment(self, email_id: str, attachment_id: str, source: str) -> dict:
        """Метаданные вложения с download_url."""
        self._activate()
        try:
            if source == "received":
                return resend.Emails.Receiving.Attachments.get(email_id, attachment_id)
            return resend.Emails.Attachments.get(email_id, attachment_id)
        except Exception as exc:
            raise self._wrap_error(exc) from exc
