"""Фабрика FastAPI-приложения."""

from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.manager import ConfigManager
from app.services.mail_service import MailService
from app.services.resend_client import ResendApiClient
from app.version import __version__
from app.web.controllers.config_controller import ConfigController
from app.web.controllers.mail_controller import MailController
from app.web.controllers.mailbox_controller import MailboxController
from app.web.controllers.page_controller import PageController


class WebApplication:
    """
    Собирает все зависимости и создаёт экземпляр FastAPI.

    Использует паттерн «composition root» — здесь создаются все сервисы
    и контроллеры, а маршруты регистрируются централизованно.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or Path(__file__).resolve().parent.parent.parent
        self._static_dir = self._base_dir / "static"

        # Слой конфигурации
        self._config_manager = ConfigManager(self._base_dir / "config.json")

        # Слой сервисов
        self._resend_client = ResendApiClient(self._config_manager)
        self._mail_service = MailService(self._config_manager, self._resend_client)

        # Слой контроллеров
        self._page_controller = PageController(self._static_dir)
        self._config_controller = ConfigController(self._config_manager)
        self._mailbox_controller = MailboxController(self._config_manager)
        self._mail_controller = MailController(self._mail_service)

    def create(self) -> FastAPI:
        """Создаёт и возвращает настроенное FastAPI-приложение."""
        app = FastAPI(
            title="Resend GUI Client",
            description="Почтовый клиент для отправки и получения писем через Resend",
            version=__version__,
        )

        api_router = APIRouter(prefix="/api")
        self._page_controller.register(app.router)
        self._config_controller.register(api_router)
        self._mailbox_controller.register(api_router)
        self._mail_controller.register(api_router)
        app.include_router(api_router)

        app.mount("/static", StaticFiles(directory=self._static_dir), name="static")
        return app
