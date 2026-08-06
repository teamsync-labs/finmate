# CI/CD — FinMate

Модель: runner → `docker save` → scp → `docker load` → `compose up` без `--build`. Registry нет.

## Workflows

| Событие | Workflow | Действие |
|---------|----------|----------|
| PR → `main` / `dev` | `ci.yml` | сборка образов + import-smoke |
| merge PR → `main` | `deploy-main.yml` | deploy **prod** |
| merge PR → `dev` | `deploy-dev.yml` | deploy **dev** (Environment пока не создаём) |
| `workflow_dispatch` | deploy-* | ручной redeploy |

## Environment `prod`

Пользователь VPS: `finmate-prod`. Хост/пути — только в GitHub Variables.

### Secrets

| Name | Значение |
|------|----------|
| `SSH_PRIVATE_KEY` | `~/.ssh/finmate_deploy_prod` |
| `POSTGRES_PASSWORD` | сырой пароль БД |
| `SECRET_KEY` | секрет приложения (JWT / sessions) |
| `ADMIN_PASSWORD` | пароль SQLAdmin |

`DATABASE_URL` **не** нужен — собирается в `scripts/vps-write-deploy-env.sh` (`postgresql://…@db:5432/…`, URL-encode пароля, `$` → `$$` для Compose).

### Variables

| Name | Смысл / пример |
|------|----------------|
| `SERVER_HOST` | IP VPS |
| `SERVER_USER` | `finmate-prod` |
| `SERVER_PATH` | каталог кода prod |
| `DATA_PATH` | каталог данных prod |
| `COMPOSE_PROJECT_NAME` | `finmate-prod` |
| `NGINX_PORT` | `3111` |
| `ACCESS_VIA_DOMAIN` | `false` до TLS |
| `APP_DOMAIN` | `finmate.space` |
| `ADMIN_USERNAME` | `admin` (опционально; дефолт в workflow) |

Опционально (есть дефолты): `POSTGRES_USER=finsight`, `POSTGRES_DB=finsight`.

### VPS

Нужны Docker, Compose plugin, **rsync**.

Пока `ACCESS_VIA_DOMAIN=false`: healthcheck `http://$SERVER_HOST:3111/health`.  
После host nginx + TLS: `ACCESS_VIA_DOMAIN=true` → `https://finmate.space/health`.
