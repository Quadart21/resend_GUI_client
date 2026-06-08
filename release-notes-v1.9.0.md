## Summary

- Новая дизайн-система: токены, UI-kit (`AppIcon`, `UiModal`, `UiAvatar`, `UiBadge`, …)
- `AppShell` — единый каркас: sidebar · список · переписка
- Переписка в формате email-карточек вместо чат-пузырей
- Inline-кomposer для ответа (сворачивается/разворачивается)
- Обновлённые sidebar, список переписок, login split-screen, модалки
- Брендинг **Kubex Mail**

## Deploy

```bash
cd ~/resend_GUI_client && git pull && docker compose --profile prod up -d --build
```
