```sh
docker compose -f docker-compose.yml exec backend bash
```

### Import ftp data

```sh
python manage.py import_ftp_download_logs import/download-ftp/downloads_202605.log
python manage.py import_ftp_download_logs import/download-sftp/downloads_sftp_202605.log
python manage.py import_ftp_auth_logs import/auth-ftp/auth-ftp-last-month_202605.log
python manage.py import_ftp_auth_logs import/auth-sftp/auth_sftp_202605.log
python manage.py sync_ftp_users_and_roles
# python manage.py mark_log_access_role
# python manage.py update_last_activity_ftp_users
```

### Import download data

```sh
python manage.py import_download_items import/download-stat/i1zk2_download_items.csv
python manage.py import_download_stat import/download-stat/i1zk2_download_stat.csv
python manage.py import_email_from_website import/users/i1zk2_users.csv
```

### build backend in localstoreg

```bash
# ── Крок 1: один раз (або при зміні requirements.txt) ──
# Запускаєш на будь-якій машині — збирає Linux wheels
docker build -f docker/config/dockerfile.backend --target wheel-builder -t backend:wheels .

# Витягуєш wheels з контейнера в docker/wheels/
docker run --rm \
  -v $(pwd)/docker/wheels:/out \
  backend:wheels \
  sh -c "cp /wheels/*.whl /out/"

# На Windows (PowerShell):
docker run --rm `
  -v ${PWD}/docker/wheels:/out `
  backend:wheels `
  sh -c "cp /wheels/*.whl /out/"

# ── Крок 2: звичайна розробка (без інтернету) ──────────
docker build --target dev -t backend:dev .

# ── Крок 3: prod build (без інтернету) ─────────────────
docker build --target prod -t backend:prod .
```
