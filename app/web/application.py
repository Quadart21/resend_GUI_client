"""Фабрика FastAPI-приложения."""

from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.manager import ConfigManager
from app.db.database import DatabaseManager
from app.repositories.email_repository import EmailRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.mail_service import MailService
from app.services.notification_service import NotificationService
from app.services.resend_client import ResendApiClient
from app.services.sync_service import SyncService
from app.version import __version__
from app.web.controllers.auth_controller import AuthController
from app.web.controllers.config_controller import ConfigController
from app.web.controllers.mail_controller import MailController
from app.web.controllers.mailbox_controller import MailboxController
from app.web.controllers.notification_controller import NotificationController
from app.web.controllers.page_controller import PageController
from app.web.controllers.user_controller import UserController
from app.web.controllers.webhook_controller import WebhookController


class WebApplication:
    """
    Собирает все зависимости и создаёт экземпляр FastAPI.

    Composition root: БД → репозитории → сервисы → контроллеры.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or Path(__file__).resolve().parent.parent.parent
        self._static_dir = self._base_dir / "static"
        self._assets_dir = self._static_dir / "assets"

        # SQLite
        self._database = DatabaseManager(self._base_dir / "data" / "resend_gui.db")

        # Конфигурация и репозитории
        self._config_manager = ConfigManager(
            db=self._database,
            legacy_json_path=self._base_dir / "config.json",
        )
        self._email_repository = EmailRepository(self._database)
        self._user_repository = UserRepository(self._database)
        self._session_repository = SessionRepository(self._database)

        # Авторизация
        self._auth_service = AuthService(self._user_repository, self._session_repository)
        self._auth_service.bootstrap_if_empty()
        self._session_repository.purge_expired()

        # Сервисы
        self._resend_client = ResendApiClient(self._config_manager)
        self._sync_service = SyncService(
            self._resend_client,
            self._email_repository,
            self._config_manager.settings_repo,
        )
        self._mail_service = MailService(
            self._config_manager,
            self._resend_client,
            self._email_repository,
            self._sync_service,
        )
        self._notification_service = NotificationService(
            self._config_manager,
            self._email_repository,
        )

        # Контроллеры
        self._page_controller = PageController(self._static_dir)
        self._auth_controller = AuthController(self._auth_service)
        self._user_controller = UserController(self._auth_service)
        self._config_controller = ConfigController(self._config_manager, self._auth_service)
        self._mailbox_controller = MailboxController(self._config_manager, self._auth_service)
        self._mail_controller = MailController(self._mail_service, self._auth_service)
        self._webhook_controller = WebhookController(self._mail_service, self._auth_service)
        self._notification_controller = NotificationController(
            self._notification_service,
            self._auth_service,
        )

    def create(self) -> FastAPI:
        """Создаёт и возвращает настроенное FastAPI-приложение."""
        app = FastAPI(
            title="Resend GUI Client",
            description="Почтовый клиент для отправки и получения писем через Resend",
            version=__version__,
        )

        api_router = APIRouter(prefix="/api")
        self._page_controller.register(app.router)
        self._auth_controller.register(api_router)
        self._user_controller.register(api_router)
        self._config_controller.register(api_router)
        self._mailbox_controller.register(api_router)
        self._mail_controller.register(api_router)
        self._webhook_controller.register(api_router)
        self._notification_controller.register(api_router)
        app.include_router(api_router)

        if self._assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=self._assets_dir), name="assets")

        return app
