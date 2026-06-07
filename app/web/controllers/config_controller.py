"""Контроллер настроек приложения."""

from fastapi import APIRouter, HTTPException, Request

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
            user = self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            _ = user
            saved = self._config.update_api_key(body.api_key)
            return {
                "ok": True,
                "has_api_key": saved.has_api_key(),
                "api_key_preview": saved.api_key_preview(),
                "mailboxes": [box.to_dict() for box in saved.mailboxes],
            }
