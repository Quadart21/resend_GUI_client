"""Контроллер входа и сессий."""

from fastapi import APIRouter, Request, Response

from app.models.dto import LoginDto
from app.models.user import User
from app.services.auth_service import AuthService, SESSION_COOKIE


class AuthController:
    """REST API: login, logout, текущий пользователь."""

    def __init__(self, auth_service: AuthService) -> None:
        self._auth = auth_service

    @staticmethod
    def _set_session_cookie(response: Response, token: str) -> None:
        response.set_cookie(
            key=SESSION_COOKIE,
            value=token,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/",
        )

    @staticmethod
    def _clear_session_cookie(response: Response) -> None:
        response.delete_cookie(key=SESSION_COOKIE, path="/")

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.post("/auth/login")
        async def login(body: LoginDto, response: Response) -> dict:
            token, user = self._auth.login(body.username, body.password)
            self._set_session_cookie(response, token)
            return {"ok": True, "user": user.to_public_dict()}

        @router.post("/auth/logout")
        async def logout(request: Request, response: Response) -> dict:
            self._auth.logout(request.cookies.get(SESSION_COOKIE))
            self._clear_session_cookie(response)
            return {"ok": True}

        @router.get("/auth/me")
        async def me(request: Request) -> dict:
            user = self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            return {"user": user.to_public_dict()}
