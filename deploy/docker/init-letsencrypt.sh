#!/usr/bin/env bash
# Получение Let's Encrypt сертификата для webmail.kubex.me (один раз)
# Запускать на сервере из корня проекта: bash deploy/docker/init-letsencrypt.sh

set -euo pipefail

DOMAIN="webmail.kubex.me"
EMAIL="${CERTBOT_EMAIL:-admin@kubex.me}"
CERT_DIR="$(cd "$(dirname "$0")/certs" && pwd)"
PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

mkdir -p "$CERT_DIR"

if [[ -f "$CERT_DIR/fullchain.pem" ]]; then
  echo "Сертификаты уже есть в $CERT_DIR"
  exit 0
fi

echo "==> Временный HTTP-only nginx для certbot..."

# Временный compose только webmail + certbot webroot
docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d webmail

cat > /tmp/nginx-certbot.conf <<'EOF'
server {
    listen 80;
    server_name webmail.kubex.me;
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    location / {
        return 200 'ok';
        add_header Content-Type text/plain;
    }
}
EOF

docker run -d --rm --name certbot-nginx \
  -p 80:80 \
  -v /tmp/nginx-certbot.conf:/etc/nginx/conf.d/default.conf:ro \
  -v certbot_www:/var/www/certbot \
  nginx:1.27-alpine

echo "==> Запрос сертификата..."
docker run --rm \
  -v certbot_www:/var/www/certbot \
  -v certbot_certs:/etc/letsencrypt \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email

docker stop certbot-nginx || true

docker run --rm \
  -v certbot_certs:/etc/letsencrypt \
  -v "$CERT_DIR:/out" \
  alpine sh -c "cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /out/ && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /out/"

echo "==> Сертификаты сохранены в $CERT_DIR"
echo "    Запустите: docker compose --profile prod up -d"
