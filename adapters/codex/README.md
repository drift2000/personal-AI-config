# Codex adapter (підготовлено, не активовано)

Codex використовує ту саму методологію з `global/`. Окремих копій змісту в репозиторії немає: `python adapters/install.py --codex` генерує файли Codex із `global/`.

## Що генерується

| Файл | Джерело | Чому так |
|---|---|---|
| `~/.codex/AGENTS.md` | `global/AGENTS.md` (з підставленим `$AI_PRIVATE_ROOT`) | Codex не підтримує імпорти в AGENTS.md і читає один глобальний файл → потрібна згенерована копія. Після змін у `global/AGENTS.md` перезапустіть `install.py --codex`; `--check --codex` покаже розбіжність. |
| `~/.codex/agents/<role>.toml` | `global/agents/<role>.md` (тіло → `developer_instructions`) | Формат custom agents Codex: `name`, `description`, `developer_instructions`. |
| `~/.agents/skills/<name>` (junction/symlink) | `global/skills/<name>` | Codex сканує `~/.agents/skills` і `.agents/skills`; symlinks підтримуються. Той самий SKILL.md, що й для Claude. |

`~/.codex/config.toml` не змінюється ніколи. Згенеровані файли містять позначку `GENERATED`; файли без неї install.py не перезаписує.

## Перевірений формат (документація Codex, станом на 2026-10)

Джерела: learn.chatgpt.com/docs/agent-configuration/agents-md, …/build-skills, …/agent-configuration/subagents, …/config-file/config-reference (колишні developers.openai.com/codex/*).

- AGENTS.md: глобально `~/.codex/AGENTS.override.md` або `AGENTS.md` (один файл), далі файли від кореня репо до cwd; ліміт `project_doc_max_bytes` = 32 KiB. Імпортів немає.
- Skills: `SKILL.md` з обов'язковими `name` і `description` (інших полів frontmatter не документовано; додаткові метадані — `agents/openai.yaml`). Тому глобальні й проєктні skills тут мають лише ці два поля.
- `[[skills.config]]` (`path`, `enabled`) — документовано для ввімкнення/вимкнення; чи реєструє він skill поза скан-каталогами — **не підтверджено**, хоча так працювало в попередньому середовищі (decision 0004 zhytlokomservis). Перевірити після активації.
- Custom agents: `~/.codex/agents/*.toml` (особисті) або `.codex/agents/` (проєктні); поля `name`, `description`, `developer_instructions`, опційно `model`, `model_reasoning_effort`, `[[skills.config]]`, `features.*`. Старіша форма `[agents.<name>] description/config_file` у config.toml ще згадується в config reference.
- **Read-only ролей у Codex не існує**: субагенти успадковують sandbox і approval батьківської сесії, `sandbox_mode` у файлі агента не перевизначається. Обмеження `architect`/`security`/`reviewer` — лише інструкціями (або `features.shell_tool = false`). Для гарантії — запускати сесію з `sandbox_mode = "read-only"`.
- Назва ролі `review` попереднього середовища → тепер `reviewer` (спільна з Claude).

## Активація (лише за окремим рішенням)

```
python adapters/install.py --check --codex   # що буде створено
python adapters/install.py --codex           # створити
```
Тест без змін у реальному домашньому каталозі: `--home <тимчасовий каталог> --codex`.
