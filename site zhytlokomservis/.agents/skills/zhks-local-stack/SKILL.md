---
name: zhks-local-stack
description: Diagnose or change the local Docker Compose environment for the Zhytlokomservis Yii application, including its launcher and service configuration.
---

# Локальне середовище Житлокомсервісу

Цей скіл описує лише локальне середовище проєкту. Для приватного контексту, брифів і рішень застосовуйте глобальний `private-project-memory`; не дублюйте тут його правила.

Перед змінами перегляньте кореневий `README.md`, `run.sh` і відповідні файли `docker/docker-compose*.yml`: актуальні Compose-файли та `run.sh` є джерелом фактичної конфігурації. Базові сервіси — frontend, backend, MariaDB, Adminer і MailHog; режими та їхні накладання визначає `run.sh`.

Враховуйте образи PHP 7.2 у `docker/frontend/Dockerfile` та `docker/backend/Dockerfile`, параметри зі зразка `.env.example` і стан доступних залежностей. Не виводьте вміст `.env` або інші секрети. Перевіряйте конфігурацію й синтаксис засобами, доступними в поточному середовищі, та пояснюйте обмеження перевірки.

`run.sh restore` імпортує останній дамп у базу, а `run.sh deploy` працює з Git і production-контейнерами. Не запускайте їх для звичайної діагностики; виконуйте лише коли таку дію явно замовлено, після перевірки цільового середовища.
