# Resend GUI Client

Почтовый веб-клиент для отправки и получения писем с вашего домена через [Resend API](https://resend.com/docs/introduction).

## Возможности

- Отправка писем (HTML / текст, CC, BCC)
- Просмотр входящих писем (Receiving)
- Просмотр отправленных и их статуса
- Ответ на входящие в той же ветке
- Локальное хранение настроек (API-ключ, адрес отправителя)

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

1. Откройте раздел **Настройки**
2. Укажите API-ключ из [Resend Dashboard](https://resend.com/api-keys)
3. Укажите email на вашем домене (например `hello@yourdomain.com`)
4. Сохраните

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
├── config/          ConfigManager — локальные настройки
├── models/          AppSettings, DTO-модели
├── services/        ResendApiClient, MailService
├── utils/           AddressParser
└── web/
    ├── application.py   WebApplication — сборка FastAPI
    └── controllers/     PageController, ConfigController, MailController
static/              HTML, CSS, JS (классы)
main.py              Точка входа
```

## Релизы

Версии публикуются на [GitHub Releases](https://github.com/Quadart21/resend_GUI_client/releases).
Текущая версия указана в файле `VERSION`.
