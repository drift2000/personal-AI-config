# Документація постачальника білінгу

## Goal and scope

Опрацювати надані ODT-матеріали про HTTP Web API та Oracle-пакет
`z$runtime_sz_utl`, перетворити їх на підтримувану документацію проєкту й
зберегти оригінали локально без додавання персональних даних до Git.

## Verified findings

- `web-api.odt` описує HTTP-операції `getZerro`, `getActualDebt`,
  `getAccountInfo`, `getLastAccountInfo`, `getAccountProv` і `getKvitInfo`.
- Поточна інтеграція сайту здійснюється лише через
  `src/common/extensions/BillingConnections.php`; Oracle-пакет напряму не
  використовується.
- Оригінали містять приклади з персональними даними. Їх перенесено до
  `docs/billing/sources/` і виключено з Git; знеособлені технічні контракти
  описано в `docs/billing/`.
- Зовнішні запити з реальними рахунками не виконувалися.

## Work status / next step

Документація готова для підтримки наявної інтеграції. Перед розширенням
контракту слід узгодити тестове середовище, прикладні дані й доступ із
власником білінгу.

## References

- `docs/billing/README.md`
- `docs/billing/web-api.md`
- `docs/billing/oracle-sz-utl.md`
