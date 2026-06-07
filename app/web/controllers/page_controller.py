"""Контроллер главной страницы SPA."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


class PageController:
    """Отдаёт собранное Vue-приложение (index.html)."""

    def __init__(self, static_dir: Path) -> None:
        self._static_dir = static_dir
        self._index = static_dir / "index.html"

    def register(self, router: APIRouter) -> None:
        """Регистрирует маршруты контроллера."""

        @router.get("/")
        async def index() -> FileResponse:
            if not self._index.exists():
                # Подсказка, если фронтенд не собран
                from fastapi.responses import HTMLResponse
                return HTMLResponse(
                    content=(
                        "<h1>Resend GUI Client</h1>"
                        "<p>Фронтенд не собран. Выполните: "
                        "<code>cd frontend && npm install && npm run build</code></p>"
                    ),
                    status_code=503,
                )
            return FileResponse(self._index)
