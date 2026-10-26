---
paths:
  - "**/*.php"
  - "**/*.twig"
  - "**/*.tpl"
  - "**/composer.json"
---

# PHP, Joomla, WordPress, OpenCart/ocStore

- Версію PHP визначає конкретний проєкт; підтримуються й legacy-проєкти на PHP 7.2. Не вимагати оновлення версії і не вважати сучасну версію за замовчуванням.
- Визначити фактичну версію PHP (Dockerfile, `composer.json` → `config.platform`/`require.php`) і не використовувати синтаксис новішої версії: typed properties (7.4), union types / `match` / named args / nullsafe (8.0), enums / readonly (8.1).
- Дотримуватися архітектури CMS, а не обходити її:
  - OpenCart/ocStore: MVC-L (`controller`/`model`/`view`/`language`), зміни ядра — через OCMOD/events, якщо проєкт так робить; БД — `$this->db->escape()`/приведення типів; `DB_PREFIX`.
  - WordPress: hooks/filters, `$wpdb->prepare()`, nonces + `current_user_can()`, `esc_html/esc_attr/esc_url`, `sanitize_*`.
  - Joomla: MVC компонентів, `$db->quote()`/`quoteName()` або prepared queries, `Session::checkToken()`, ACL `authorise()`, `HTMLHelper`/`htmlspecialchars` для виводу.
- Не редагувати vendor/core-файли CMS без явного погодження; якщо проєкт уже так робить — зафіксувати це.
- Вивід помилок і debug — не вмикати на production; не залишати `var_dump`/`print_r`.
- Перевірка: `php -l` у контейнері з правильною версією; наявні тести/лінтери проєкту.
