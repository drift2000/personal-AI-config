---
paths:
  - "**/Dockerfile*"
  - "**/docker-compose*.yml"
  - "**/docker-compose*.yaml"
  - "**/compose*.yml"
  - "**/nginx/**"
  - "**/*.sh"
---

# Docker, Compose, Nginx

- Фактичну конфігурацію визначають Compose-файли, Dockerfile, `.env.example` і скрипти запуску проєкту. Перед змінами прочитати їх повністю, включно з overlay-файлами (`*.dev.yml`, `*.prod.yml`).
- Не виводити значення з `.env`; посилатися на назви змінних.
- Зберігати версії образів, які використовує проєкт (PHP/Node/Python/MySQL). Оновлення версії — окреме погоджене рішення.
- Не додавати секрети в образ (ARG/ENV/COPY `.env`). Credentials — через env/secrets під час запуску.
- Перевірка: `docker compose config` для синтаксису; запуск/перезбірку контейнерів — лише якщо це безпечно для локальних даних.
- Заборонено без доручення: `down -v`, видалення volumes, `system prune`, restore/deploy-скрипти, дії на production-хостах.
- Nginx: після змін — `nginx -t` у контейнері; не розширювати `location` з доступом до службових каталогів (`.git`, `storage`, `system`, `config`).
- Shell-скрипти: `set -euo pipefail` у нових скриптах, коректне лапкування шляхів (у шляхах бувають пробіли), LF-кінці рядків.
