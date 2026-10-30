### Запуск Docker-контейнера

1. Запускаємо команду (збірка без використання кешу)

```sh
docker-compose build --no-cache
```

2. Далі запускаємо сам контейнер

```sh
docker-compose up -d
```

## Перебудова Docker-контейнера

1. Зупинка Docker контейнера (видалення контейнерів)

```sh
docker-compose down
```

2. Видалення даних Docker

```sh
docker system prune -a
docker image prune
docker volume prune
```

5. Rebuild without using cache

```sh
docker-compose build --no-cache
```

6. Start Container

```sh
docker-compose up -d
```

## Запус терміналу в контейнере

```sh
docker-compose up -d --build backend

docker-compose exec backend bash
or
docker compose -f docker-compose.yml exec backend bash
docker compose -f docker-compose.yml exec frontend bash

docker compose -f docker-compose.yml exec frontend npm install @mui/material @emotion/react @emotion/styled

python manage.py makemigrations
python manage.py migrate
```

### import commands

```sh
python manage.py import_ftp_download_logs import/ftp-download/downloads_202606.log
python manage.py import_ftp_download_logs import/ftp-download/downloads_sftp_202606.log
python manage.py import_ftp_auth_logs import/ftp-auth/auth-ftp-last-month_202606.log
python manage.py import_ftp_auth_logs import/ftp-auth/auth_sftp_202606.log
python manage.py sync_ftp_users_and_roles

python manage.py import_email_from_website import/db-info/i1zk2_users.csv
python manage.py import_download_items import/db-info/i1zk2_download_items.csv
python manage.py import_download_stat import/db-info/i1zk2_download_stat.csv



python manage.py update_email_dates import/users/i1zk2_users.csv

python manage.py import_email_from_website import/users/i1zk2_users.csv
```

### dupm DB

```sh
pg_dump -U enamine_user -d enamine_db -F p -f backup.sql
docker compose -f docker/docker-compose.yml exec postgres pg_dump -U enamine_user enamine_db > dump.sql
docker compose -f docker/docker-compose.yml exec -t postgres pg_dump -U enamine_user -d enamine_db -t client1_company > client1_company_dump.sql

docker compose -f docker/docker-compose.yml exec -i postgres psql -U enamine_user -d enamine_db -f dump2.sql
```

```sh
docker compose -f docker/docker-compose.yml exec -i postgres pg_restore -U enamine_user -d enamine_db --clean --no-owner < /data/db/dump/init.sql.gz
```

### clean DB on the server before restore dump

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

### start container without cache

```sh
docker compose -f docker/docker-compose.dev.yml build --no-cache
docker compose -f docker/docker-compose.dev.yml up
```

```sh
chmod +x run.sh
```

Show client migrations:
docker-compose exec backend python manage.py showmigrations client
Inspect columns:
docker-compose exec -T postgres psql -U enamine_user -d enamine_db -c "SELECT column_name,data_type FROM information_schema.columns WHERE table_name='client_company';"
(similar queries for client_email, client_user, client_company_candidate)
Apply SQL changes:
docker-compose exec -T postgres psql -U enamine_user -d enamine_db -c "BEGIN; ALTER TABLE client_company ADD COLUMN additional_info text DEFAULT '' NOT NULL; ALTER TABLE client_email ADD COLUMN additional_info text DEFAULT '' NOT NULL; ALTER TABLE client_user ADD COLUMN additional_info text DEFAULT '' NOT NULL; ALTER TABLE client_company DROP COLUMN region; ALTER TABLE client_company_candidate DROP COLUMN region; COMMIT;"
Mark migration as applied:
docker-compose exec -T postgres psql -U enamine_user -d enamine_db -c "INSERT INTO django_migrations (app, name, applied) VALUES ('client','0013_remove_company_region_remove_companycandidate_region_and_more', now());"
Run migrations:
docker-compose exec backend python manage.py migrate --noinput

```sh
python manage.py export_domains import/hubspot-crm-exports-test-view-by-maryna-2026-03-23.csv --output import/export_domains.csv
```

```
І так, проект почав розростатись і з'явилось багато фнукціоналу, за котрими треба слудкувати. Тому, я думаю, нам треба додати агентів, котрі будуть слідкавати за функціоналом. дивитись. щоб при створені онового не поламався старий. Будуть вести документацію. Мати відповідкі скіли до проекту.
Тепер детальніше про проект.
Опис: Це маленька CRM система, котра відображає статистику по скачуванням з сайту, зведена таблиця по різним інтеграція і доступам та великий об'єм даних по компаніям, email користувачів та їх ПІП. (в майбутньому, може доповнь)
Стек: frontend - React.js, спілкується з backend по API. Backend - Django 4x. Для роботи з API використовується Swagger. DB - postgres
Backend: Має адмін частину для наповрення та коренції даних. Розділений на application:
- client - робота з компаніями, email, іменами користувачів, доменами та статичною таблицею по країнам. В чйому роздіді багато чого зв'зано між собою, тому він потребує максимально детальної документації.
- download - добота з імпортованими даними по скачування з сайту. При імпорті дані співставляються та зв'зуються з даними з client. Що полегшує подальшу обробку даних та роботу з ними.
- ftp - це розділ з інтеграціями, де заносяться всі можливі інтеграції, для відображення в одному місці. А також імпортується логи авторизації та скачування, щомісячно. Для відстідковування активності клієнтів по інтеграції.
- once - тут зібрані скрипти, котрі використвуються один раз, наприклад для імпорту якихось даних і більше не використовуються. Я не впевнений, що такий розділ потрібен, чи це можна зробити якось більш практично. Тут на твоі розсуд.
- Також є статичні сторінки, котрі виводять дані для моніторингу даних в системі.
Frontend: Звичайні сторінки, котрі будуються з даних отриманих через API. Система не потребує авторизації і тому подібного.
Все розгорнуто в Docker. Релізи заливаються в репозіторій, з котрого потім заливається оновлення на сервер. На сервері теж все працює в Docker.


- Пріорітет, від більш пріорітетних до меньш: client, ftp, download
- Агенти повині бути локальні. Я з ними буду працювати локально, тільки при розробці.
- Я ще не знаю, що потрібно автоматизувати по пріорітету. Я хотів би автоматизувати документацію, створення шаблоних (які повторюються) блоків, стандартизувати логіку (наприклад стандартизувати логіку логування при роботі скриптів в backend. Це зараз частково зроблено. Чи наприклад логіку побудови таблиці на frontend)
- CI поки не планую.
- Markdown думає буде на даному етапі достатньо. Далі будемо дивитись
```
