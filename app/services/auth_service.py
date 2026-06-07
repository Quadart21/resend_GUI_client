"""Сервис авторизации и проверки прав."""

import os

from fastapi import HTTPException

from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.password_service import PasswordService

SESSION_COOKIE = "resend_session"


class AuthService:
    """Логин, сессии, bootstrap администратора, проверка доступа к ящикам."""

    def __init__(
        self,
        user_repo: UserRepository,
        session_repo: SessionRepository,
    ) -> None:
        self._users = user_repo
        self._sessions = session_repo

    def bootstrap_if_empty(self) -> None:
        """Создаёт первого администратора, если пользователей ещё нет."""
        if self._users.count() > 0:
            return

        username = os.getenv("ADMIN_USERNAME", "admin").strip()
        password = os.getenv("ADMIN_PASSWORD", "admin").strip()
        if not username or not password:
            raise RuntimeError(
                "Нет пользователей. Задайте ADMIN_USERNAME и ADMIN_PASSWORD."
            )

        self._users.create(
            username=username,
            password_hash=PasswordService.hash_password(password),
            is_admin=True,
            mailbox_ids=[],
        )

    def login(self, username: str, password: str) -> tuple[str, User]:
        """Проверяет учётные данные и создаёт сессию."""
        user = self._users.get_by_username(username)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")

        stored = self._users.get_password_hash(user.id)
        if not stored or not PasswordService.verify_password(password, stored):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")

        token = self._sessions.create(user.id)
        return token, user

    def logout(self, token: str | None) -> None:
        if token:
            self._sessions.delete(token)

    def get_user_by_token(self, token: str | None) -> User | None:
        if not token:
            return None
        user_id = self._sessions.get_user_id(token)
        if not user_id:
            return None
        user = self._users.get_by_id(user_id)
        if not user or not user.is_active:
            return None
        return user

    def require_user(self, token: str | None) -> User:
        user = self.get_user_by_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Требуется авторизация")
        return user

    def require_admin(self, user: User) -> User:
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Доступ только для администратора")
        return user

    def require_mailbox_access(self, user: User, mailbox_id: str) -> None:
        if not user.can_access_mailbox(mailbox_id):
            raise HTTPException(status_code=403, detail="Нет доступа к этому ящику")

    def create_user(
        self,
        username: str,
        password: str,
        *,
        is_admin: bool = False,
        mailbox_ids: list[str] | None = None,
    ) -> User:
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        return self._users.create(
            username=username,
            password_hash=PasswordService.hash_password(password),
            is_admin=is_admin,
            mailbox_ids=mailbox_ids or [],
        )

    def update_user(
        self,
        user_id: str,
        *,
        password: str | None = None,
        is_admin: bool | None = None,
        is_active: bool | None = None,
        mailbox_ids: list[str] | None = None,
    ) -> User:
        password_hash = None
        if password is not None:
            if len(password) < 4:
                raise ValueError("Пароль должен быть не короче 4 символов")
            password_hash = PasswordService.hash_password(password)
        user = self._users.update(
            user_id,
            password_hash=password_hash,
            is_admin=is_admin,
            is_active=is_active,
            mailbox_ids=mailbox_ids,
        )
        if password is not None or is_active is False:
            self._sessions.delete_for_user(user_id)
        return user

    def delete_user(self, user_id: str, actor: User) -> None:
        if actor.id == user_id:
            raise ValueError("Нельзя удалить самого себя")
        self._sessions.delete_for_user(user_id)
        self._users.delete(user_id)

    def list_users(self) -> list[User]:
        return self._users.list_all()
