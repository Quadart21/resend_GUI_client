# Resend GUI Client

Почтовый веб-клиент для отправки и получения писем с вашего домена через [Resend API](https://resend.com/docs/introduction).

## Возможности

- **Несколько почтовых ящиков** — каждый адрес на домене как отдельный ящик
- **Цепочки переписки** — входящие и исходящие объединяются по теме
- Отправка писем от имени выбранного ящика
- Чат-интерфейс просмотра переписки с быстрым ответом
- Локальное хранение настроек (API-ключ, ящики)

## Требования

- Python 3.11+
- API-ключ Resend
- Верифицированный домен в Resend
- Настроенный Receiving для приёма входящих ([документация](https://resend.com/docs/dashboard/receiving/introduction))

## Установка на сервер (Linux)

```bash
git clone https://github.com/Quadart21/resend_GUI_client.git
cd resend_GUI_client
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
# Через скрипт
chmod +x start.sh
./start.sh

# Или напрямую
uvicorn main:app --host 0.0.0.0 --port 8080
```

Откройте в браузере: `http://<IP-сервера>:8080`

## Настройка

1. Откройте **Настройки** (иконка внизу сайдбара)
2. Укажите API-ключ из [Resend Dashboard](https://resend.com/api-keys)
3. Добавьте один или несколько ящиков (например `hello@domain.com`, `support@domain.com`)
4. Выберите ящик в сайдбаре — отобразятся его переписки

Файл `config.json` создаётся автоматически и не попадает в git.

## Systemd (опционально)

```bash
sudo cp deploy/resend-gui.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable resend-gui
sudo systemctl start resend-gui
```

## Архитектура (ООП)

```
app/
├── config/          ConfigManager — локальные настройки и ящики
├── models/          AppSettings, Mailbox, DTO-модели
├── services/        ResendApiClient, MailService, ThreadService
├── utils/           AddressParser, EmailHelper
└── web/
    ├── application.py   WebApplication — сборка FastAPI
    └── controllers/     Page, Config, Mailbox, Mail
static/              HTML, CSS, JS (классы)
main.py              Точка входа
```

## Релизы

Версии публикуются на [GitHub Releases](https://github.com/Quadart21/resend_GUI_client/releases).
Текущая версия указана в файле `VERSION`.
