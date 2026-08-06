# Хостовый nginx (вне compose)

Каталог уезжает на VPS с rsync в `$SERVER_PATH/deploy/host-nginx/`.
Конфиг в `/etc/nginx/...` **не** подхватывается сам — копируем вручную.

## Файлы

| Файл | Назначение |
|------|------------|
| `finmate-prod.conf` | vhost → `127.0.0.1:3111` |
| `maintenance.html` | страница 502/503/504 на время recreate стека |

## Порядок на VPS (root)

### 1. HTTP vhost

Нужны: хостовый `nginx`, открытые `80`/`443` в UFW. Файлы на диске — после деплоя (rsync).

```bash
# SERVER_PATH = GitHub Variable (каталог кода prod), обычно:
#   /var/www/finmate/prod
install -d -m 755 /etc/nginx/sites-available /etc/nginx/sites-enabled
cp /var/www/finmate/prod/deploy/host-nginx/finmate-prod.conf \
  /etc/nginx/sites-available/finmate-prod.conf
ln -sfn /etc/nginx/sites-available/finmate-prod.conf \
  /etc/nginx/sites-enabled/finmate-prod.conf
nginx -t && systemctl reload nginx
```

Проверка:

```bash
curl -fsS -H 'Host: finmate.space' http://127.0.0.1/health
# снаружи: http://finmate.space/health → {"status":"ok","database":"connected"}
```

Если ISPmanager держит `listen <IP>:80` на чужом vhost — в нашем conf тоже
пропиши `listen <IP>:80` (не голый `listen 80`), иначе запросы уйдут в default_server.

### 2. TLS (certbot)

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d finmate.space -d www.finmate.space
```

После успеха скопируй обновлённый `/etc/nginx/sites-available/finmate-prod.conf`
обратно в репо (`deploy/host-nginx/`) — источник правды с SSL-блоками.
Проверь, что www→apex редирект на **https** (certbot иногда оставляет `http://`).

### 3. Закрыть прямой доступ по порту compose

GitHub Environment `prod`: `ACCESS_VIA_DOMAIN=true` → Redeploy (Deploy Prod).
Compose-nginx станет на `127.0.0.1:3111`. Healthcheck — `https://finmate.space/health`.

Затем под root:

```bash
ufw delete allow 3111/tcp
# или по номеру: ufw status numbered && ufw delete <N>
ufw status numbered
ss -tlnp | grep 3111
```

Ожидаем: `:3111` только `127.0.0.1`.
