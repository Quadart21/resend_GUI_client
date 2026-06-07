#!/usr/bin/env bash
# Скрипт запуска Resend GUI Client на сервере

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Сборка Vue-фронтенда, если static/index.html отсутствует
if [ ! -f static/index.html ] && [ -f frontend/package.json ]; then
  echo "Сборка фронтенда (Vue + Tailwind)..."
  (cd frontend && npm ci && npm run build)
fi

if [ -d "venv" ]; then
  source venv/bin/activate
fi

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}"
