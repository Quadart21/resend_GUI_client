"""Контроллер настроек приложения."""

from fastapi import APIRouter

from app.config.manager import ConfigManager
from app.models.dto import ConfigUpdateDto


class ConfigController:
    """REST API для управления конфигурацией."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self._config = config_manager

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/config")
        async def get_config() -> dict:
            return self._config.public_view()

        @router.post("/config")
        async def update_config(body: ConfigUpdateDto) -> dict:
            saved = self._config.update(
                api_key=body.api_key,
                from_email=body.from_email,
                from_name=body.from_name,
            )
            return {
                "ok": True,
                "from_email": saved.from_email,
                "from_name": saved.from_name,
                "has_api_key": saved.has_api_key(),
                "api_key_preview": saved.api_key_preview(),
            }
