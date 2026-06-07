# Resend GUI Client

Почтовый веб-клиент для отправки и получения писем с вашего домена через [Resend API](https://resend.com/docs/introduction).

## Стек

| Слой | Технологии |
|------|------------|
| Frontend | **Vue 3**, **Tailwind CSS**, Vite |
| Backend | Python, FastAPI, **SQLite** (OOP, REST API) |

## Возможности

- **Несколько почтовых ящиков** — каждый адрес на домене как отдельный ящик
- **Цепочки переписки** — входящие и исходящие объединяются по теме
- Отправка писем от имени выбранного ящика
- Чат-интерфейс просмотра переписки с быстрым ответом
- Локальное хранение настроек (API-ключ, ящики)

## Требования

- Python 3.11+
- Node.js 20+ (для сборки фронтенда)
- API-ключ Resend
- Верифицированный домен в Resend
- Настроенный Receiving для приёма входящих ([документация](https://resend.com/docs/dashboard/receiving/introduction))

## Установка на сервер (Linux)

```bash
git clone https://github.com/Quadart21/resend_GUI_client.git
cd resend_GUI_client
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Сборка фронтенда
cd frontend && npm ci && npm run build && cd ..
```

## Запуск

```bash
# Автоматически соберёт фронтенд, если нужно
chmod +x start.sh && ./start.sh

# Или напрямую (после npm run build)
uvicorn main:app --host 0.0.0.0 --port 8080
```

Откройте: `http://<IP-сервера>:8080`

## Разработка

```bash
# Терминал 1 — API
uvicorn main:app --host 127.0.0.1 --port 8080 --reload

# Терминал 2 — Vue dev-сервер (hot reload, proxy /api)
cd frontend
npm install
npm run dev
```

**PowerShell** (в старых версиях `&&` не работает — используйте `;` или отдельные строки):

```powershell
cd frontend; npm run dev
```

Dev-сервер: `http://localhost:5173`

## Настройка

1. **Настройки** → API-ключ из [Resend Dashboard](https://resend.com/api-keys)
2. Добавьте ящики (`hello@domain.com`, `support@domain.com`)
3. Выберите ящик в сайдбаре → переписки этого ящика

Данные хранятся в `data/resend_gui.db` (не сбрасываются при перезапуске).  
Старый `config.json` автоматически мигрирует в БД.

### Webhook для входящих (опционально)

В [Resend → Webhooks](https://resend.com/webhooks):

- URL: `https://ваш-сервер:8080/api/webhooks/resend`
- Событие: `email.received`

## Архитектура

```
frontend/src/        Vue 3 + Tailwind
app/
├── db/              DatabaseManager (SQLite)
├── repositories/    Settings, Mailbox, Email
├── config/          ConfigManager
├── services/        SyncService, MailService, ResendApiClient
└── web/controllers/ REST API + webhook
data/resend_gui.db   Ящики, письма, API-ключ
static/              Сборка Vite
main.py              Точка входа
```

## Релизы

[GitHub Releases](https://github.com/Quadart21/resend_GUI_client/releases) · версия в `VERSION`
