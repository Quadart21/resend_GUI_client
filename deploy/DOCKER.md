# Деплой через Docker — webmail.kubex.me

Полная инструкция для production на VPS с Docker Compose.

## Схема

```
Internet → https://webmail.kubex.me (:443)
              ↓
         nginx (контейнер)
              ↓
         webmail (контейнер, FastAPI + Vue)
              ↓
         volume resend_gui_data → SQLite
              ↓
         Resend API + webhook
```

---

## 1. Требования

- VPS (Ubuntu 22.04+)
- Docker 24+ и Docker Compose v2
- DNS: **A-запись** `webmail.kubex.me` → IP сервера
- Аккаунт [Resend](https://resend.com) с API-ключом и доменом для почты

---

## 2. Установка Docker (если ещё нет)

```bash
curl -fsSL https://get.docker.com | sh && systemctl enable docker && systemctl start docker && docker compose version
```

---

## 3. Установка одной командой

**С нуля** (Docker + git + SSL + запуск). DNS `webmail.kubex.me` → IP сервера, порт **80** свободен:

```bash
curl -fsSL https://get.docker.com | sh && systemctl enable docker && systemctl start docker && git clone https://github.com/Quadart21/resend_GUI_client.git && cd resend_GUI_client && chmod +x deploy/docker/init-letsencrypt.sh && CERTBOT_EMAIL=ваш@email.com bash deploy/docker/init-letsencrypt.sh && docker compose --profile prod up -d --build
```

В `/opt`:

```bash
curl -fsSL https://get.docker.com | sh && systemctl enable docker && systemctl start docker && mkdir -p /opt/resend-gui && cd /opt/resend-gui && git clone https://github.com/Quadart21/resend_GUI_client.git . && chmod +x deploy/docker/init-letsencrypt.sh && CERTBOT_EMAIL=ваш@email.com bash deploy/docker/init-letsencrypt.sh && docker compose --profile prod up -d --build
```

**Репозиторий уже склонирован** (как у вас сейчас):

```bash
curl -fsSL https://get.docker.com | sh && systemctl enable docker && systemctl start docker && cd ~/resend_GUI_client && chmod +x deploy/docker/init-letsencrypt.sh && CERTBOT_EMAIL=ваш@email.com bash deploy/docker/init-letsencrypt.sh && docker compose --profile prod up -d --build
```

Сертификаты появятся в `deploy/docker/certs/` (`fullchain.pem`, `privkey.pem`).

---

## 4. Обновление

```bash
cd /opt/resend-gui && git pull && docker compose --profile prod up -d --build
```

---

## 5. Проверка

```bash
docker compose ps && docker compose logs --tail=20 webmail && curl -I https://webmail.kubex.me
```

Откройте: **https://webmail.kubex.me**

---

## 6. Первичная настройка в GUI

1. **Настройки** → API-ключ Resend (`re_...`)
2. Добавьте **почтовые ящики** (email на вашем домене в Resend)
3. **Resend → Webhooks** → Add Webhook:
   - URL: `https://webmail.kubex.me/api/webhooks/resend`
   - Event: `email.received`

Данные сохраняются в Docker volume `resend_gui_data` и **не пропадают** при `docker compose restart`.

---

## 7. Полезные команды

```bash
# Статус
docker compose ps

# Логи приложения
docker compose logs -f webmail

# Логи nginx
docker compose logs -f nginx

# Перезапуск
docker compose --profile prod restart

# Остановка
docker compose --profile prod down

# Обновление после git pull
cd /opt/resend-gui && git pull && docker compose --profile prod up -d --build

# Ручная синхронизация писем с Resend
curl -X POST https://webmail.kubex.me/api/sync
```

---

## 8. Бэкап SQLite

```bash
# Скопировать БД из volume на хост
docker compose exec webmail cat /app/data/resend_gui.db > backup/resend_gui_$(date +%F).db
```

Или:

```bash
docker run --rm -v resend_gui_data:/data -v $(pwd)/backup:/backup alpine \
  cp /data/resend_gui.db /backup/resend_gui_$(date +%F).db
```

---

## 9. Обновление SSL (каждые ~90 дней)

```bash
# Продлить certbot volume и скопировать в deploy/docker/certs/
docker run --rm \
  -v certbot_certs:/etc/letsencrypt \
  -v $(pwd)/deploy/docker/certs:/out \
  alpine sh -c "cp /etc/letsencrypt/live/webmail.kubex.me/fullchain.pem /out/ && cp /etc/letsencrypt/live/webmail.kubex.me/privkey.pem /out/"

docker compose --profile prod restart nginx
```

---

## 10. Режим без nginx (только для отладки)

```bash
docker compose up -d --build
# Приложение: http://127.0.0.1:8080
```

Nginx на хосте может проксировать на `127.0.0.1:8080`.

---

## 11. Resend: домен для почты

| Что | Где |
|-----|-----|
| GUI (этот проект) | `https://webmail.kubex.me` |
| Отправка/приём почты | Домен в Resend (напр. `kubex.me`) |
| Webhook | `https://webmail.kubex.me/api/webhooks/resend` |

GUI и почтовый домен — **разные вещи**.  
`webmail.kubex.me` — только интерфейс.  
Ящики в GUI должны совпадать с адресами на домене в Resend.

---

## 12. Troubleshooting

| Проблема | Решение |
|----------|---------|
| `502 Bad Gateway` | `docker compose logs webmail` — дождитесь `healthy` |
| Пустая страница | Пересоберите: `docker compose --profile prod up -d --build` |
| Нет HTTPS | Проверьте файлы в `deploy/docker/certs/` |
| Webhook не работает | URL только HTTPS, событие `email.received` |
| Данные пропали | Не используйте `docker compose down -v` (удалит volume!) |

---

## 13. Чеклист

- [ ] DNS `webmail.kubex.me` → IP сервера
- [ ] Docker установлен
- [ ] `init-letsencrypt.sh` выполнен
- [ ] `docker compose --profile prod up -d --build`
- [ ] https://webmail.kubex.me открывается
- [ ] API-ключ и ящики в GUI
- [ ] Webhook Resend настроен
- [ ] Тест: отправка + входящее письмо
