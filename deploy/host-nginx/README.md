# Хостовый nginx (вне compose)

Каталог попадает на VPS через rsync в `$SERVER_PATH/deploy/host-nginx/`.
Конфиг в `/etc/nginx/...` сам не подхватывается — копирование в sites-available вручную.

## Файлы

| Файл | Назначение |
|------|------------|
| `finmate-prod.conf` | vhost → `127.0.0.1:3111` |
| `maintenance.html` | страница 502/503/504 на время recreate стека |

## Порядок на VPS (root)

### 1. HTTP vhost

Требования: хостовый `nginx`, в UFW открыты `80`/`443`.

Если rsync/deploy ещё не довёз каталог (например недоступен Actions) — каталог копируется с машины с репо:

```bash
# с рабочей машины (ключ и хост — по окружению)
ssh finmate-prod@SERVER 'mkdir -p /var/www/finmate/prod/deploy'
scp -r deploy/host-nginx \
  finmate-prod@SERVER:/var/www/finmate/prod/deploy/
```

На VPS (root):

```bash
install -d -m 755 /etc/nginx/sites-available /etc/nginx/sites-enabled
cp /var/www/finmate/prod/deploy/host-nginx/finmate-prod.conf \
  /etc/nginx/sites-available/finmate-prod.conf
ln -sfn /etc/nginx/sites-available/finmate-prod.conf \
  /etc/nginx/sites-enabled/finmate-prod.conf
nginx -t && systemctl reload nginx
```

Проверка:

```bash
# если nginx слушает только публичный IP (ISPmanager) — Host на IP, не на 127.0.0.1
curl -fsS -H 'Host: finmate.space' http://127.0.0.1/health \
  || curl -fsS -H 'Host: finmate.space' http://SERVER_IP/health
# снаружи: http://finmate.space/health → {"status":"ok","database":"connected"}
# /health отвечает на GET; curl -I (HEAD) может дать 405 — это ожидаемо
```

Если ISPmanager держит `listen <IP>:80` на чужом vhost — в conf этого проекта тоже
нужен `listen <IP>:80` (не голый `listen 80`), иначе запросы уходят в default_server.

### 2. TLS (certbot)

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d finmate.space -d www.finmate.space
```

После выпуска сертификата обновлённый `/etc/nginx/sites-available/finmate-prod.conf`
возвращается в репо (`deploy/host-nginx/`) как источник правды с SSL-блоками.
У www→apex редирект должен быть на **https** (certbot иногда оставляет `http://`).
Не добавлять `ipv6only=on` только на один из `listen [::]:443` — будет conflict.

После правки conf в репо — выкладка на VPS:

```bash
cp /var/www/finmate/prod/deploy/host-nginx/finmate-prod.conf \
  /etc/nginx/sites-available/finmate-prod.conf
# и копия в $SERVER_PATH/deploy/host-nginx/ при необходимости
nginx -t && systemctl reload nginx
```

### 3. Закрыть прямой доступ по порту compose

В GitHub Environment `prod` выставить `ACCESS_VIA_DOMAIN=true` и выполнить Redeploy (Deploy Prod).
Compose-nginx слушает `127.0.0.1:3111`. Healthcheck — `https://finmate.space/health`.

Затем под root:

```bash
ufw delete allow 3111/tcp
# или по номеру: ufw status numbered && ufw delete <N>
ufw status numbered
ss -tlnp | grep 3111
```

Ожидаемый результат: `:3111` только на `127.0.0.1`.
