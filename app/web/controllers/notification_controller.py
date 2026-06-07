"""Контроллер проверки новых входящих (для push-уведомлений в браузере)."""

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.auth_service import AuthService, SESSION_COOKIE
from app.services.notification_service import NotificationService


class NotificationController:
    """REST API: новые письма с момента последней проверки."""

    def __init__(
        self,
        notification_service: NotificationService,
        auth_service: AuthService,
    ) -> None:
        self._notifications = notification_service
        self._auth = auth_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/notifications/inbound")
        async def check_inbound(
            request: Request,
            since: str = Query(..., description="ISO-время последней проверки (UTC)"),
        ) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            if not since.strip():
                raise HTTPException(status_code=400, detail="Параметр since обязателен")
            return self._notifications.check_inbound(user, since.strip())
