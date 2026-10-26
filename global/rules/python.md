---
paths:
  - "**/*.py"
  - "**/requirements*.txt"
  - "**/pyproject.toml"
---

# Python, Django, Django REST Framework

- Версії Python/Django/DRF — з `requirements*`/`pyproject.toml`/Dockerfile; не використовувати API новіших версій.
- Django: бізнес-логіка поза views, якщо проєкт так структурований; ORM замість raw SQL (raw — лише з параметрами); `select_related`/`prefetch_related` проти N+1.
- Міграції: генерувати `makemigrations`, переглядати вміст, не редагувати застосовані міграції; data-міграції — з `reverse_code`.
- DRF: явні `permission_classes` і `authentication_classes`; серіалізатори з явним `fields` (не `__all__` для чутливих моделей); пагінація для списків.
- Налаштування: секрети з env, `DEBUG=False` поза локальним середовищем, `ALLOWED_HOSTS`, CSRF не вимикати.
- Перевірка: наявні тести (`manage.py test`/pytest), `manage.py check`, лінтер проєкту.
