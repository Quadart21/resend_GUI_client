"""Контроллер настроек приложения."""

from fastapi import APIRouter, Request

from app.config.manager import ConfigManager
from app.models.dto import ConfigUpdateDto
from app.services.auth_service import AuthService, SESSION_COOKIE


class ConfigController:
    """REST API для управления конфигурацией (API-ключ — только админ)."""

    def __init__(self, config_manager: ConfigManager, auth_service: AuthService) -> None:
        self._config = config_manager
        self._auth = auth_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/config")
        async def get_config(request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            return self._config.public_view(user)

        @router.post("/config")
        async def update_config(body: ConfigUpdateDto, request: Request) -> dict:
            self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            saved = self._config.update_settings(body.api_key, body.webhook_secret)
            return {
                "ok": True,
                "has_api_key": saved.has_api_key(),
                "api_key_preview": saved.api_key_preview(),
                "has_webhook_secret": bool(self._config.resolve_webhook_secret()),
                "webhook_secret_preview": self._config.webhook_secret_preview(),
                "mailboxes": [box.to_dict() for box in saved.mailboxes],
            }
