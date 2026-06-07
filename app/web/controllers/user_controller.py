"""Контроллер управления пользователями (только админ)."""

from fastapi import APIRouter, HTTPException, Request

from app.models.dto import UserCreateDto, UserUpdateDto
from app.services.auth_service import AuthService, SESSION_COOKIE


class UserController:
    """CRUD пользователей и назначение ящиков."""

    def __init__(self, auth_service: AuthService) -> None:
        self._auth = auth_service

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/users")
        async def list_users(request: Request) -> dict:
            admin = self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            _ = admin
            users = self._auth.list_users()
            return {"users": [u.to_public_dict() for u in users]}

        @router.post("/users")
        async def create_user(body: UserCreateDto, request: Request) -> dict:
            self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            try:
                user = self._auth.create_user(
                    body.username,
                    body.password,
                    is_admin=body.is_admin,
                    mailbox_ids=body.mailbox_ids,
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"ok": True, "user": user.to_public_dict()}

        @router.put("/users/{user_id}")
        async def update_user(user_id: str, body: UserUpdateDto, request: Request) -> dict:
            self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            try:
                user = self._auth.update_user(
                    user_id,
                    password=body.password,
                    is_admin=body.is_admin,
                    is_active=body.is_active,
                    mailbox_ids=body.mailbox_ids,
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"ok": True, "user": user.to_public_dict()}

        @router.delete("/users/{user_id}")
        async def delete_user(user_id: str, request: Request) -> dict:
            actor = self._auth.require_admin(
                self._auth.require_user(request.cookies.get(SESSION_COOKIE))
            )
            try:
                self._auth.delete_user(user_id, actor)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"ok": True}
