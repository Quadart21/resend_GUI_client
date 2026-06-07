"""Контроллер главной страницы."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


class PageController:
    """Отдаёт статическую HTML-страницу клиента."""

    def __init__(self, static_dir: Path) -> None:
        self._static_dir = static_dir

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/")
        async def index() -> FileResponse:
            return FileResponse(self._static_dir / "index.html")
