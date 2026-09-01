#!/usr/bin/env bash
# Пишет .env для Docker Compose (не bash source).
# Не использовать printf %q — как в geek-tik / ai-sous-chef.
set -euo pipefail

ENV_FILE="${1:?usage: vps-write-deploy-env.sh <outfile>}"

: >"$ENV_FILE"

write_kv_compose() {
  local key="$1"
  local value="$2"
  local escaped="$value"
  escaped="${escaped//\\/\\\\}"
  escaped="${escaped//\"/\\\"}"
  escaped="${escaped//\$/\$\$}"
  printf '%s="%s"\n' "$key" "$escaped" >>"$ENV_FILE"
}

: "${IMAGE_PREFIX:?}"
: "${IMAGE_TAG:?}"
: "${COMPOSE_PROJECT_NAME:?}"
: "${POSTGRES_USER:?}"
: "${POSTGRES_PASSWORD:?}"
: "${POSTGRES_DB:?}"
: "${SECRET_KEY:?}"
: "${ADMIN_USERNAME:?}"
: "${ADMIN_PASSWORD:?}"
: "${TELEGRAM_BOT_TOKEN:?}"
: "${BOT_SERVICE_KEY:?}"
: "${CONSENT_PUBLIC_BASE:?}"
: "${NGINX_PORT:?}"
: "${NGINX_BIND:?}"
: "${ACCESS_VIA_DOMAIN:?}"
: "${APP_DOMAIN:?}"
: "${APP_PUBLIC_URL:?}"
: "${HEALTHCHECK_URL:?}"
: "${DATA_PATH:?}"

pass_enc="$(
  POSTGRES_PASSWORD="$POSTGRES_PASSWORD" python3 -c \
    'import os, urllib.parse; print(urllib.parse.quote(os.environ["POSTGRES_PASSWORD"], safe=""))'
)"
# FinMate backend — sync SQLAlchemy (postgresql://), хост сервиса `db`
DATABASE_URL="postgresql://${POSTGRES_USER}:${pass_enc}@db:5432/${POSTGRES_DB}"

write_kv_compose IMAGE_PREFIX "$IMAGE_PREFIX"
write_kv_compose IMAGE_TAG "$IMAGE_TAG"
write_kv_compose COMPOSE_PROJECT_NAME "$COMPOSE_PROJECT_NAME"

write_kv_compose DEBUG "false"
write_kv_compose POSTGRES_USER "$POSTGRES_USER"
write_kv_compose POSTGRES_PASSWORD "$POSTGRES_PASSWORD"
write_kv_compose POSTGRES_DB "$POSTGRES_DB"
write_kv_compose DATABASE_URL "$DATABASE_URL"

write_kv_compose SECRET_KEY "$SECRET_KEY"
write_kv_compose ADMIN_USERNAME "$ADMIN_USERNAME"
write_kv_compose ADMIN_PASSWORD "$ADMIN_PASSWORD"

# Telegram bot
write_kv_compose TELEGRAM_BOT_TOKEN "$TELEGRAM_BOT_TOKEN"
write_kv_compose BOT_SERVICE_KEY "$BOT_SERVICE_KEY"
write_kv_compose CONSENT_PUBLIC_BASE "$CONSENT_PUBLIC_BASE"
write_kv_compose TELEGRAM_PROXY "${TELEGRAM_PROXY:-}"

write_kv_compose NGINX_PORT "$NGINX_PORT"
write_kv_compose NGINX_BIND "$NGINX_BIND"
write_kv_compose ACCESS_VIA_DOMAIN "$ACCESS_VIA_DOMAIN"
write_kv_compose APP_DOMAIN "$APP_DOMAIN"
write_kv_compose APP_PUBLIC_URL "$APP_PUBLIC_URL"
write_kv_compose HEALTHCHECK_URL "$HEALTHCHECK_URL"

write_kv_compose DATA_PATH "$DATA_PATH"

chmod 600 "$ENV_FILE"
