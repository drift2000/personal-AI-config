# Розгортання і синхронізація

## Вимоги

Git, Python 3.8+ (у PATH або вказати `--python`), Claude Code (CLI або VS Code extension). На Windows symlinks не потрібні — використовуються junctions.

## Новий комп'ютер

1. Клонувати поруч із робочими проєктами (конвенція `<parent>/.private/<project_name>/`):
   ```
   git clone git@github.com:drift2000/personal-AI-config.git ~/source/.private
   ```
   Якщо проєкти лежать в іншому каталозі — клонувати в `<той каталог>/.private`.
2. Подивитися, що буде змінено:
   ```
   python ~/source/.private/adapters/install.py --check
   ```
3. Встановити:
   ```
   python ~/source/.private/adapters/install.py
   ```
   Скрипт створює посилання, блок у `~/.claude/CLAUDE.md`, SessionStart hook у `~/.claude/settings.json` (з бекапом) і `core.hooksPath` приватного репо. Наявні файли без маркерів не змінює — повідомляє CONFLICT і показує, що додати вручну.
4. Перевірити: `install.py --check` → «Усе на місці.»; нова сесія Claude Code у будь-якому проєкті → `/memory` показує імпорт `global/AGENTS.md`, `/agents` — 5 ролей, у списку skills є `private-project-memory`.
5. Codex (лише за рішенням): `install.py --check --codex`, потім `install.py --codex`.

## Щоденна синхронізація

```
cd ~/source/.private
git pull --ff-only                     # перед роботою
python adapters/install.py --check     # якщо додавались global skills
# ... робота ...
git status
python global/scripts/audit_index.py   # повна перевірка index
git add <конкретні файли>              # не git add -A наосліп
git diff --cached
git commit -m "..."                    # pre-commit перевірить staged
git push                               # лише після перевірки
```

Зміни `global/AGENTS.md`, `global/rules/`, skills та агентів діють у нових сесіях Claude без перевстановлення (імпорт і посилання). Перевстановлення потрібне лише для нового global skill або для Codex.

## Не синхронізується

`~/.claude/` (credentials, sessions, history, projects/memory, cache), `~/.codex/` (auth.json, sqlite, sessions), `<project>/local/`, `.env*`, ключі, дампи, архіви. Видимість GitHub-репо має бути **private**; навіть так не зберігати тут клієнтські дані та секрети. Якщо секрет потрапив у коміт — вважати скомпрометованим і замінити (переписування історії — окремим рішенням).
