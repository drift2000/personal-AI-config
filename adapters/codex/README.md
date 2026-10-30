# Codex adapter

Цей адаптер підключає спільну методологію з `global/` до Codex без копіювання її змісту та без зміни Claude. Активація кожного профілю виконується окремо за перевіреним планом.

## Архітектура

| Об’єкт профілю | Джерело / призначення |
|---|---|
| `$CODEX_HOME/AGENTS.md` | symlink на `global/AGENTS.md`; наступна сесія бачить зміни методології одразу |
| `$CODEX_HOME/agents/personal-ai-*.toml` | по одній тонкій TOML-обгортці на кожен `global/agents/*.md` (ім’я й опис — з його frontmatter, спільного з Claude). Обгортки посилаються на актуальні тіла ролей, не копіюють їх |
| `~/.agents/skills/private-project-memory` | symlink на спільний skill; проєктні skills лишаються у власних `.agents/skills` |
| `$CODEX_HOME/hooks.json` | нативні `SessionStart` і `SubagentStart`, що викликають `context_hook.py` |

Hook використовує спільний resolver із `global/hooks/private_context.py`. Він передає лише шлях та короткий перелік релевантних приватних документів, не їхній вміст. Для Git worktree він визначає основний checkout; чужий клон або вкладений Git-репозиторій не отримує контекст за збігом імені.

Глобальні ролі названі `personal-ai-*`, тому не перекривають проєктні Joomla-ролі з іншими іменами. Нативні субагенти успадковують права батьківської сесії; інструкція ролі не є технічним обмеженням sandbox.

## Сумісність

Runtime installer і hooks потребують Python 3.8+; шлях із `--python` записується в hook-команду й має лишатися доступним після активації. Ізольовані regression-тести також не використовують API новіше за Python 3.8, але додатково потребують Git для worktree-сценаріїв.

Codex adapter підтримує лише POSIX-системи (Linux/macOS): symlink-транспорт і quoting hook-команди не реалізовані для Windows. На Windows `--check`, `--prepare` та активація Codex завершуються конфліктом до запису. Це обмеження не стосується Claude adapter, який використовує junctions.

## Підготовка та активація

`--codex` ніколи не викликає Claude installer, Git hooks або змінює `config.toml`, permissions, trust, MCP чи plugin settings. За замовчуванням профіль береться з `CODEX_HOME`, інакше з `~/.codex`.

```bash
# Лише повна перевірка і список змін.
python adapters/install.py --codex --check

# Створити незмінний план, не торкаючись профілю.
python adapters/install.py --codex --prepare local/codex-plan.json \
  --replace AGENTS.md --replace skill:private-project-memory

# Лише після перевірки плану та окремого погодження.
python adapters/install.py --codex --activate local/codex-plan.json
```

`--replace` обмежений наявними `AGENTS.md` і skill `private-project-memory`. Каталог skill дозволено замінити лише тоді, коли весь його snapshot точно збігається зі спільним джерелом; змінений `SKILL.md` або будь-який додатковий файл блокують активацію. Сторонній symlink можна перепризначити тільки за явним `--replace`, без видалення його цільових даних. Symlink у батьківському шляху, `AGENTS.override.md`, дублікати skill та всі інші сторонні об’єкти також блокують активацію. План містить fingerprint початкового стану, тому застарілий або відредагований план відхиляється до першого запису.

Для повністю ізольованої перевірки використовуйте `--home /tmp/…`; цей режим ігнорує поточний `CODEX_HOME` і не торкається робочого профілю.

## Відкат

Кожна зміна має окремий manifest у `$CODEX_HOME/.personal-ai-config/backups/<id>/manifest.json`. Він містить лише об’єкти, якими володіє адаптер; `config.toml`, auth, history, SQLite, sessions і сторонні файли не копіюються.

```bash
python adapters/install.py --codex --rollback \
  "$CODEX_HOME/.personal-ai-config/backups/<id>/manifest.json"
```

Rollback спершу перевіряє всі fingerprints установлених об’єктів і backup. Якщо користувач змінив будь-який з них, він відмовляється від часткового відновлення. Manifest після успішного відкату зберігається як запис операції.

## Перевірки після активації

Відкрийте **нову** Codex-сесію в основному checkout та linked worktree і перевірте: глобальні інструкції, п’ять `personal-ai-*` ролей, глобальний і проєктні skills, а також повідомлення hook без вмісту `context.md`. Trust для hooks налаштовується Codex окремо; адаптер його не змінює. Далі виконайте контрольну задачу, яка перевіряє автономну реалізацію в межах ADR і чесний статус ручної функціональної перевірки.

В ізольованому профілі підтверджено Codex CLI discovery AGENTS symlink, user skill і обох hook-реєстрацій. Фактичне виконання trusted hooks, завантаження ролей у конкретному клієнті та поведінка моделі в живій задачі потребують перевірки після погодженої активації.

Discovery skill і доступ shell до його шляху — різні перевірки. [Офіційна документація OpenAI](https://developers.openai.com/codex/skills/) підтверджує user-scope `$HOME/.agents/skills` і підтримку symlink-каталогів. Якщо клієнт показує skill у каталозі, але команда читання отримує `ENOENT` для `~/.agents/skills/...`, спершу перевірте filesystem sandbox поточної сесії: він може приховувати каталог, хоча профільний symlink встановлений правильно. Це не виправляється повторною активацією.
