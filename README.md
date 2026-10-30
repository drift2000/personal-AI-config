# personal-AI-config (PRIVATE)

Приватна конфігурація AI-assisted development і приватна база знань проєктів.
Ніщо звідси не копіюється в робочі репозиторії без окремого явного дозволу.

## Рівні

| Рівень | Де | Що |
|---|---|---|
| A — Global | `global/` | `AGENTS.md` (єдине джерело глобальних правил), `rules/` (за стеком), `skills/`, `agents/`, `hooks/`, `scripts/`, `templates/` |
| B — Private | `<project_name>/` у корені | `context.md`, `briefs/`, `decisions/`, `history/`, `skills/`, `agents/`, `archive/`, `local/` (не синхронізується; машинозалежні/тимчасові файли без конфіденційних даних) |
| C — Project | репозиторій проєкту | `AGENTS.md` + `CLAUDE.md` (`@AGENTS.md`), `.claude/`, README — лише погоджене для команди; шаблон у `global/templates/repo/` |

`<project_name>` = ім'я каталогу проєкту (конвенція `<parent>/.private/<project_name>/`). Імена `global` та `adapters` зарезервовані.

## Як інструменти це бачать

**Claude Code** (`python adapters/install.py --claude`):
- `~/.claude/CLAUDE.md` — маркерний блок з `@<root>/global/AGENTS.md` (імпорт: зміни діють одразу в нових сесіях).
- `~/.claude/skills/<skill>` → `global/skills/<skill>` (junction на Windows / symlink).
- `~/.claude/agents/personal-ai-config` → `global/agents`; `~/.claude/rules/personal-ai-config` → `global/rules`.
- `~/.claude/settings.json` → SessionStart hook `global/hooks/private_context.py`: визначає проєкт за cwd і повідомляє шлях та перелік приватних матеріалів, skills і агентів (без вмісту). Якщо проєкт неоднозначний — контекст не підставляється.

**Codex** — див. `adapters/codex/README.md`. Адаптер використовує symlink на спільні правила й skills, тонкі обгортки ролей та нативні hooks; його активація має окремий підготовлений план і rollback manifest.

## Захист

- `.gitignore` — секрети, дампи, архіви, кеші, `local/`.
- `.githooks/pre-commit` → `global/scripts/audit_index.py --staged`.
- `python global/scripts/audit_index.py` — повна перевірка вже відстежуваних файлів (вміст з index, файли, що відстежуються попри .gitignore). Запускати перед push і періодично.
- Жоден із цих засобів не є абсолютним: перед комітом переглядайте `git diff --cached`. Політика зберігання даних із [глобальних правил](global/AGENTS.md#1-приватність--private-by-default) діє також у `local/`.

## Розширення

- Новий універсальний skill → `global/skills/<name>/SKILL.md` (frontmatter лише `name`, `description`) → `python adapters/install.py --claude`.
- Новий проєктний приватний skill/агент → `<project>/skills/<name>/SKILL.md`, `<project>/agents/<role>.md` (hook знайде автоматично).
- Нове правило стеку → `global/rules/<topic>.md` з `paths:` frontmatter + рядок у розділі 8 `global/AGENTS.md`.

Розгортання й синхронізація — `SETUP.md`.
