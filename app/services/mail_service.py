"""Бизнес-логика работы с почтой."""

from typing import Any

from fastapi import HTTPException

from app.config.manager import ConfigManager
from app.models.dto import ReplyEmailDto, SendEmailDto
from app.services.resend_client import ResendApiClient
from app.utils.address_parser import AddressParser


class MailService:
    """Координирует отправку, получение и ответы на письма."""

    def __init__(self, config_manager: ConfigManager, resend_client: ResendApiClient) -> None:
        self._config = config_manager
        self._client = resend_client
        self._parser = AddressParser()

    def _require_from_address(self) -> str:
        """Проверяет наличие адреса отправителя."""
        address = self._config.load().from_address()
        if not address:
            raise HTTPException(
                status_code=400,
                detail="Укажите адрес отправителя в настройках (ваш домен).",
            )
        return address

    @staticmethod
    def _require_body(html: str, text: str, error_message: str) -> None:
        """Проверяет, что тело письма не пустое."""
        if not html.strip() and not text.strip():
            raise HTTPException(status_code=400, detail=error_message)

    def send_email(self, dto: SendEmailDto) -> dict[str, Any]:
        """Отправляет новое письмо."""
        from_addr = self._require_from_address()
        to_list = self._parser.parse(dto.to)
        if not to_list:
            raise HTTPException(status_code=400, detail="Укажите получателя.")

        self._require_body(dto.html, dto.text, "Текст письма не может быть пустым.")

        params: dict[str, Any] = {
            "from": from_addr,
            "to": to_list,
            "subject": dto.subject.strip(),
        }
        if dto.html.strip():
            params["html"] = dto.html
        if dto.text.strip():
            params["text"] = dto.text

        cc = self._parser.parse(dto.cc)
        bcc = self._parser.parse(dto.bcc)
        reply_to = self._parser.parse(dto.reply_to)
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc
        if reply_to:
            params["reply_to"] = reply_to

        result = self._client.send(params)
        return {"ok": True, "data": result}

    def list_sent(self, after: str | None = None) -> dict:
        """Список отправленных писем."""
        return self._client.list_sent(after)

    def get_sent(self, email_id: str) -> dict:
        """Детали отправленного письма."""
        return self._client.get_sent(email_id)

    def list_received(self, after: str | None = None) -> dict:
        """Список входящих писем."""
        return self._client.list_received(after)

    def get_received(self, email_id: str) -> dict:
        """Детали входящего письма."""
        return self._client.get_received(email_id)

    def reply_to_received(self, email_id: str, dto: ReplyEmailDto) -> dict[str, Any]:
        """Отвечает на входящее письмо в той же ветке (In-Reply-To)."""
        from_addr = self._require_from_address()
        self._require_body(dto.html, dto.text, "Текст ответа не может быть пустым.")

        original = self._client.get_received(email_id)
        original_from = original.get("from", "")
        original_subject = original.get("subject") or "(без темы)"
        message_id = original.get("message_id")

        subject = (
            original_subject
            if original_subject.lower().startswith("re:")
            else f"Re: {original_subject}"
        )

        params: dict[str, Any] = {
            "from": from_addr,
            "to": [original_from] if isinstance(original_from, str) else original_from,
            "subject": subject,
        }
        if dto.html.strip():
            params["html"] = dto.html
        if dto.text.strip():
            params["text"] = dto.text
        if message_id:
            params["headers"] = {"In-Reply-To": message_id}

        result = self._client.send(params)
        return {"ok": True, "data": result}
