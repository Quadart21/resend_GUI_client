"""FastAPI-зависимости для авторизации."""

from fastapi import Request

from app.models.user import User
from app.services.auth_service import AuthService, SESSION_COOKIE


class AuthDependencies:
    """Фабрика Depends для текущего пользователя и прав."""

    def __init__(self, auth_service: AuthService) -> None:
        self._auth = auth_service

    def current_user(self, request: Request) -> User:
        token = request.cookies.get(SESSION_COOKIE)
        return self._auth.require_user(token)

    def admin_user(self, request: Request) -> User:
        user = self.current_user(request)
        return self._auth.require_admin(user)
