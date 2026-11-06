# site regulation — поточний контекст

## Поточний стан

- Продуктова ціль: Chem Regulations — зведена БД хімічних речовин під заборонами/контролем у різних країнах, з пошуком за структурою, назвою тощо. Бек — імпорт регулювань (окремий скрипт на кожне джерело: парсинг → імпорт → enrichment), версіонування документів; фронт — пошук; планується API. Деталі — `briefs/2026-05-25-chem-regulations.md`.
- Поточний етап (за кодом, 2026-10-29): імпорти `import_us_dea_csa` (PDF), `import_us_ca_oehha_prop65` (CSV); PDF-інструменти та `pubchem.py` у `src/core/` — частина незакомічена. Функціональну готовність не перевіряв.
- Стек: Django 4.2, DRF, PostgreSQL 16, nginx, pdfplumber/PyMuPDF (`src/requirements.txt`). Автотестів немає.
- Запуск: `./run.sh [dev|prod] [gateway] <command>`, див. README.md, `docker-compose*.yml`.
- Каталог джерел у Django (2026-11-05, гілка `feature/regulation-sources-catalog`, не закомічено): одна нова модель `RegulationSource` (довідкова, незмінна; НЕ пов'язана з `RegulationDocument`; в адмінці лише inline у Regulation — рішення користувача; окремі довідники Authority/Tag користувач відхилив як заплутані), нові поля `Regulation` (slug, category, effect, authority — текст, legal_basis, identifiers, languages, list_parts), міграція 0003 (перегенерована); головна `/` (core.HomeView) з переходом у каталог; разовий `import_regulation_catalog` (повторюваний до задовільного результату, далі імпортів не буде); сторінка `/catalog/` (серверний рендер, групи/матриця/джерела, login_required, LOGIN_URL=admin:login); тести `regulations/tests.py` (9). US-CA заноситься як US. Команди імпорту DEA/Prop65 не змінювались (рішення користувача); каталог прив'язується до їхніх записів за їхніми ключами. Імпортовано в dev-БД: 33 регулювання, 46 джерел (5 запропонованих). `RegulationSource.formats` (міграції 0004–0008, 2026-11-05/06; формат xml_api розділено на xml/json/api, наявні -> xml; усі рядки форматів позначено «потрібна перевірка», імпорт зі старих полів теж так ставить; на сторінці — синій бейдж + жовтий ⚠) — рядки `{format, url, needs_verification}` замість списків кодів; `alt_formats` злито (рядки з needs_verification) і видалено; per-format is_suggested користувач прибрав; `needs_verification` джерела лишено як «Зміст/посилання джерела не звірено» (0006 зняла його там, де перевірку позначено на форматах; імпорт так само не дублює); в адмінці — власний віджет (рядок на формат, «+ Додати формат»; без nested-inline бібліотек); url формату — задел для перевірок оновлень, url джерела НЕ підставляється (рішення користувача), заповнюється вручну.
- Дані каталогу (проміжні): `data/import/regulation-sources.json` (33 регулювання / 41 документ із двох експортів MindMeister-мапи «Regulated»: v1 — `data/import/Untitled-1.html` у git, локально видалений; v2 — розгорнутий, надісланий у чаті) + `index.html` (групи / матриця / документи). Невідомий вміст: гілка UN Convention (5 підвузлів не відрендерено в обох експортах), TSCA, Excise, CN-переліки, «Виведення з ринку» — без посилань.

## Обмеження та ризики

- Дедуплікація речовин — за InChIKey; історію не видаляти, лише статуси; enrichment — окремий замінний модуль (бриф).
- Розбіжності код ↔ бриф (2026-10-29, не виправлялись):
  - немає SHA256-перевірки змін; DEA створює нову версію при кожному запуску, Prop 65 — завжди v1;
  - DEA не позначає `removed` речовини, яких немає в новій версії; PubChem-enrichment вбудований в імпорт;
  - DEA зберігає PDF у `/app/regulations-catalog` і логи в `/app/logs` — обидва шляхи не змонтовані в `docker-compose.dev.yml` (змонтовано `/app/catalog`, `/var/logs`), тобто файли губляться при перестворенні контейнера;
  - PDF/CSV із `docker_data/catalog` і `docker_data/import` закомічені в git, хоча бриф каже тримати їх поза git;
  - `src/core/models_regulations.py` — старий дубль моделей без міграцій, імпортується з `core/models.py`;
  - `src/core/us_proposition_65.py` — незакомічена копія команди Prop 65 (з preview JSON); яка версія основна — не з'ясовано.

## AI-матеріали

- `skills/regulation-import`, `skills/pdf-table-parsing`, `agents/regulation-import.md` — адаптовано 2026-10-29 для Claude Code і Codex (frontmatter `name`/`description`, зміст звірено з кодом). Hook `private_context.py` показує їх в обох інструментах.
- `archive/2026-05-github-copilot/` — оригінальні Copilot-файли з `.github/` репозиторію (видалені з репо 2026-10-29, у git-історії лишаються). Описують задуману, а не фактичну структуру (`src/import/<source>/parser.py`, `scripts/import_runner.py`, pytest, `logs/imports/`).

## Відкриті питання та наступні дії

- Закомітити видалення `.github/` і `README.local.md` з репозиторію (окрема гілка).
- Вирішити, що робити з розбіжностями вище (кожна — окрема задача).

## Посилання

- `briefs/2026-05-25-chem-regulations.md` — бізнес-вимоги та модель даних
- `briefs/2026-06-04-dea-csa-pdf-parser.md` — постановка PDF-парсера DEA CSA (колишній `README.local.md`)
