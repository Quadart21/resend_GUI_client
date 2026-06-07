"""
Точка входа Resend GUI Client.

Запуск локально или на сервере:
    python main.py
    uvicorn main:app --host 0.0.0.0 --port 8080
"""

import uvicorn

from app.web.application import WebApplication

# Экземпляр приложения для uvicorn (main:app)
application = WebApplication()
app = application.create()


def run() -> None:
    """Запускает встроенный ASGI-сервер."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
    )


if __name__ == "__main__":
    run()
