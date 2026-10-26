---
name: zhks-receipts
description: Investigate, change, or verify account payment receipt generation and its billing response handling in the Zhytlokomservis Yii application.
---

# Квитанції Житлокомсервісу

Цей скіл описує лише домен квитанцій проєкту. Для приватного контексту, брифів і рішень застосовуйте глобальний `private-project-memory`; не дублюйте тут його правила.

Починайте з `src/frontend/controllers/AccountController.php` (`actionCheck`), `src/common/extensions/BillingConnections.php` (`getKvitInfo`) та `src/frontend/views/account/check.php`. Контролер перевіряє доступ і дату, отримує дані білінгу та формує PDF; шаблон використовує секції `acc_info`, `acc_srv` та `acc_sub`.

Вивчайте поточний код перед змінами. Окремо перевіряйте успішну відповідь, помилки й неповні дані, а також відображення PDF. У режимі розробки або на localhost помилка білінгу може замінюватися прикладом із `src/common/fixtures/kvit-info.example.json` з позначкою `is_example`; враховуйте це під час діагностики та не сприймайте приклад за відповідь реального сервісу.

Використовуйте знеособлені або прикладні дані. Не запускайте запити до зовнішнього білінгу з реальними особовими рахунками без належних даних і дозволу в межах завдання. Повідомляйте, які сценарії та фактичне формування PDF вдалося перевірити.
