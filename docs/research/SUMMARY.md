# Сводка Этапа 0 (исследование)

Дата: 2026-11-09 (второй проход, по исходникам). Статус: **ГОТОВО** с оговорками в §5.

> Как читать. «Код» — исходники, прочитанные как текст из клонов `git clone --depth 50` в отдельные папки вне проекта (D-004). «README» — только README. Ничего не запускалось, зависимости не ставились, релизы и бинарники не скачивались. Разделы I и J — только README через raw. Живых запросов к маркетам не было: пометки «проверено на живом ответе» нет ни у одного факта. Ни одна комиссия не проверена (D-009).

## 1. Что прочитано

| Репо | Задание | Что прочитано | Коммит / дата | Лицензия | Доверие | Отчёт |
|---|---|---|---|---|---|---|
| topcvetok/telegram-gift-watch | A | весь код, конфиг, тесты/фикстуры, workflows, история | 05f658a / 2026-11-01 | нет | среднее–высокое как источник идей | `topcvetok__telegram-gift-watch.md` |
| bleach-hub/portalsmp | B | весь код + история | 77fb217 / 2025-08-07 | MIT | среднее, домен устарел | `bleach-hub__portalsmp.md` |
| bleach-hub/aportalsmp | B.4 | весь код | d1daafd / 2025-11-30 | нет файла; MIT на PyPI; **D-013: использовать разрешено** | среднее | `bleach-hub__aportalsmp.md` |
| bleach-hub/tonnelmp | C | весь код + история | 68064f7 / 2025-07-07 (код 2025-06-17) | MIT | среднее, **может быть устаревшим** | `bleach-hub__tonnelmp.md` |
| TheBrainAir/amrkt | D | весь код + история | 2a4dbf5 / 2026-03-22 | MIT | среднее | `thebrainair__amrkt.md` |
| boostNT/MRKT-API, Portals-API, Tonnel-API | D, E | README (это весь репо) + история | 2026-02…03 | нет | среднее (документация) | `boostNT__*.md` |
| tgmrkt-api (PyPI) | D | только JSON-метаданные PyPI | 0.1.0 / 2025-11-04 | MIT (классификатор) | низкое, исходников нет | `pypi__tgmrkt-api.md` |
| kloveren/morgan-gift-plugins | F | весь код ключевых плагинов | 37637eb / 2026-03-27 | MIT | среднее; торговые плагины — антипример | `kloveren__morgan-gift-plugins.md` |
| bohd4nx/gifts-buyer | G | **недоступен** (удалён/скрыт; варианты имён проверены) | — | — | — | `bohd4nx__gifts-buyer.md` |
| bohd4nx/gifts-tracker | H | весь код + история | a243c21 / 2026-08-13 | нет | среднее | `bohd4nx__gifts-tracker.md` |
| maxktz/telegram-gifts-radar | H | весь код + миграции + история (первоисточник) | 1ec0fc7 / 2025-01-27 | MIT | среднее | `maxktz__telegram-gifts-radar.md` |
| OnyxTarantulaLoop, SilentOverlordBrace, smashguidetram, Townkibarrier | I | только README (raw, main) | — | «MIT © SilentOverlordBrace» на чужих ник | **ПОДОЗРИТЕЛЬНО** | по одному на репо |
| watchflowguide/tonnel-telegram-gifts-sniper | I | **недоступен** (404) | — | — | — | `watchflowguide__….md` |
| icfpztaorrmf/portals-nft-sniper | J | только README (копия обрезана на ~14,5 КБ) | — | — | **ПОДОЗРИТЕЛЬНО, вероятная малварь** | `icfpztaorrmf__….md` |
| Kirilka4345/ton-telegram-gifts-sniper-bot | J | только README | — | — | низкое / подозрительно (платный модуль за перевод) | `Kirilka4345__….md` |
| DAAMCS/gift-parser | J | только README | — | — | низкое, к флипу не относится | `DAAMCS__gift-parser.md` |
| Закрытые сервисы | K | пропущено по решению владельца (скриншоты приложит сам в `ux/`) | — | — | — | `ux/README.md` |

Признаки малвари в разделе I: ссылка «.zip», ведущая на `.exe` в релизах; инструкция обойти SmartScreen; «только Windows» из‑за «packaged companion runtime»; README Onyx и Silent совпадают на 334 из 340 строк; `git clone` указывает на другие репо; автозапуск через `schtasks`. В разделе J (icfpztaorrmf): `.exe` с внешней страницы, импорт ключа кошелька, «mempool Ethereum» для off-chain маркета TON.

## 2. Матрица «функция → откуда берём → наш модуль»

| Функция | Источник | Наш модуль | Что известно | Статус |
|---|---|---|---|---|
| Клиент Portals (чтение) | aportalsmp (D-013), topcvetok | `markets/portals.py` | `portal-market.com/api`; `nfts/search`, `collections`, `collections/floors`, `collections/filters`, `nfts/{id}`, `market/actions/`; без авторизации работают search/collections/nfts/{id}; цены — строки TON | **известно из кода** |
| Portals: покупка/листинг/баланс/вывод | aportalsmp, portalsmp | `markets/portals.py` (только описание до Этапа 7) | `POST nfts`, `nfts/bulk-list`, `nfts/{id}/list`, `users/wallets/`, `users/wallets/withdraw`; успех покупки по `total_purchased` | известно из кода |
| Клиент MRKT (чтение) | amrkt, boostNT, topcvetok (до b0e81f2) | `markets/mrkt.py` | `/auth`, `/gifts/saling`, `/gifts/collections`, `/feed`, `/gifts/gift/{id}`, `/balance`; nanoTON; заголовки `Authorization` + `Cookie access_token` + `Referer cdn.tgmrkt.io` | **известно из кода** |
| MRKT: покупка/листинг | amrkt | `markets/mrkt.py` (описание) | `POST /gifts/buy {"Ids"}` — **без цены**; `/gifts/sale`, `/sale/cancel`, `/sale/change-price` | известно из кода; soft/hard — нет |
| Клиент Tonnel (чтение) | tonnelmp, topcvetok | `markets/tonnel.py` | `gifts2.tonnel.network/api/pageGifts`, `filterStats`, `saleHistory`, `balance/info`; цены TON float; impersonate | из кода; tonnelmp проверить на актуальность |
| Tonnel: события | topcvetok | `markets/tonnel.py` | WS `wss://gifts.coffin.meme/api/marketplace/ws` + догонка `GET /api/marketplace/events?after=` | **найдено** (раньше пробел); D-011 пересмотреть |
| Tonnel: покупка/листинг | tonnelmp | `markets/tonnel.py` (описание) | `gifts.coffin.meme/api/buyGift/{id}`, `listForSale`, `cancelSale`; токен `wtf` (AES от timestamp) | из кода 2025-06, возможно устарело |
| Получение initData | portalsmp/aportalsmp, amrkt | `markets/auth.py` (Telethon) | `requestAppWebView`: Portals `@portals`/`market`, MRKT `@mrkt`/`app`; вырезка `tgWebAppData` + `unquote`; Tonnel — бот/short_name **не найдены** | известно для Portals и MRKT |
| Флор по сопоставимым | topcvetok + кластерный флор (I) | `pricing/floor.py` | topcvetok: флор = min остальных, кластер N (5 коллекция / 3 модель и фон), разброс N-го ≤ 8% / 20%, свой лот исключён. Раздел I: кластер ≥3 в +10%, доверие high/med/low, понижение при скачке > 25%/ч, запасной путь медиана 3 дешёвых → модель → символ → коллекция | **известно**, проектируем по AGENTS.md §8 + эти правила |
| Сигнал «ниже флора» | topcvetok | `rules/` | скидка ≥ 15%, прибыль ≥ 100 ₽, ROI ≥ 15% после резерва 2%, флор ≥ 1000 ₽, лот ≤ 2000 ₽; основание «коллекция» по умолчанию выключено | известно из кода |
| Проверка продажами 24 ч | topcvetok | `pricing/sales.py` | ≥3 продаж за 24 ч по тому же основанию → `resale = min(флор, медиана)`; источники: Tonnel `sale.completed` (WS), MRKT `/feed` type Sale; Portals — только `sales_24h_count` (у нас: `market/actions/` с `action_types=buy`, проверить) | известно |
| Оценка Telegram | MTProto | `pricing/tg_value.py` | §3 ниже; раздел I: «выше средней и последней продажи при low-флоре → спросить» | подтверждено документацией |
| Комиссии, net | раздел I (заявлено), tonnelmp README, фикстура topcvetok | `pricing/fees.py` | MRKT ≈2% надбавка (фикстура), Tonnel +10% (README), Portals 0/5% (заявлено) — `MARKETS.md` §6 | **не проверено** (D-009) |
| Алиасы коллекций, спред | morgan-gift-plugins | `pricing/aliases.py` | таблицы для Portals/MRKT/Tonnel там нет (11 алиасов по on-chain адресам); нормализация lower + без пробелов/`_`/`-`; спред `(max−min)/min` без комиссий | строим сами из `collections` маркетов |
| Резервный флор | Giftstat (morgan) | `pricing/` | `api.giftstat.app/current/collections/floor?marketplace=…`, без ключа; v2 с флорами по маркетам | идея, лимиты неизвестны |
| Красивые номера | topcvetok | `rules/traits.py` | `len(set(digits)) ≤ 3` (настраивается 1–10) | известно |
| Монохром | topcvetok (Clue) | `rules/traits.py` | `app.clue.tg/api/mono/resolve?url=<slug-n>` → `score`, порог 80, кэш 30 дней; свой расчёт возможен (фон по углам картинки Fragment + доминирующий цвет модели, ΔE) — в коде нет | Clue как внешний сигнал; свой — позже |
| Режимы, предохранители, `/doctor` | раздел I (README), AGENTS.md | `execution/`, `bot/` | DRY_RUN-замок, live 24 ч, лимиты по all-in под локом, fail-closed на NaN, брейкеры, `/panic` в БД, кнопки со сроком жизни, lock-файл процесса, запись `unknown` до запроса | требования |
| Пуши + «ПРОДАНО» | topcvetok, radar | `bot/` | храним `(market, gift_id, chat_id, message_id, offer_price)`; `editMessageText` с `🔴 ПРОДАНО`, кнопки снимаются; антидубль: повтор только при строго меньшей цене | известно из кода |
| Новые подарки магазина | gifts-tracker, radar | (позже) | `payments.getStarGifts(hash)`, `StarGiftsNotModified`, 10–15 с | не MVP |

## 3. Проверка MTProto: `payments.getUniqueStarGiftValueInfo`

Основано на страницах core.telegram.org (метод и конструктор, схема слоя 212), прочитанных через результаты поиска; прямое открытие страницы заблокировано allowlist; поля сверены с зеркалами (MadelineProto, Pyrogram-forks, gotd).

- Сигнатура: `payments.getUniqueStarGiftValueInfo#4365af6b slug:string = payments.UniqueStarGiftValueInfo`. Параметр один — `slug` коллекционного подарка (из `starGiftUnique`, то есть из ссылки на подарок).
- Доступно **только пользователям**, боты не могут. Схема доступна с **слоя 212**. Ошибка: `400 STARGIFT_SLUG_INVALID`.
- Результат `payments.uniqueStarGiftValueInfo#512fe446`: `currency` (string, фиатная валюта по ISO 4217), `value` (long, оценочная стоимость), `initial_sale_date`, `initial_sale_stars`, `initial_sale_price`; необязательные: `last_sale_date`, `last_sale_price`, `floor_price`, `average_price`, `listed_count`, `fragment_listed_count`, `fragment_listed_url`; флаги `last_sale_on_fragment`, `value_is_average` (значение посчитано как среднее по проданным подаркам того же типа, иначе — по цене продажи этого подарка).
- Все суммы — «в наименьшей единице валюты `currency`», то есть **фиат (локализованная валюта аккаунта), а не TON и не Stars** (кроме `initial_sale_stars`). Для сопоставления с ценой в TON нужен курс, это добавляет погрешность.
- «Подарки того же типа» (`floor_price`, `average_price`, `listed_count`) — официальное описание не уточняет, коллекция это или модель/трейты. Нужна проверка на живых ответах.
- Практический вывод: годится как **вспомогательный независимый сигнал** (последняя/средняя цена продаж по данным Telegram и флор перепродаж в Telegram), но не как единственный флор. Нужны живая пользовательская сессия, слой Telethon ≥ 212 (проверка версии библиотеки не выполнялась) и slug каждого подарка.


## 4. Риски

1. **Неофициальные API.** Все пути — обратная разработка Mini App. Домен Portals уже менялся дважды; tonnelmp не обновлялся с 2025-06; topcvetok за 3 недели переключил MRKT на сторонний агрегатор. Каждый путь подтверждаем живым ответом на Этапе 2 и держим в одном месте (`markets/*.py`).
2. **Покупка MRKT без цены.** `POST /gifts/buy {"Ids"}` не передаёт цену — купим по текущей, даже если её подняли. В `execution.spend()` нужна повторная проверка цены непосредственно перед запросом и лимит на all-in (Этап 7).
3. **Успех покупки Portals не по HTTP-коду**, а по `total_purchased`/`purchase_results[].status`. Ответы Tonnel на покупку известны только из подозрительного README.
4. **Защита Tonnel.** Cloudflare (403 без имитации TLS) и токен `wtf` с парольной фразой фронтенда, которая может меняться.
5. **`gifts.coffin.meme`** — сторонний домен, через который идут события и деньги Tonnel. По косвенным признакам это бэкенд Tonnel, но владелец не установлен.
6. **Сроки токенов** не известны; перевыпуск по 401 (D-005).
7. **ToS и бан аккаунта.** Автоматизация пользовательской сессии; клиенты, выдающие себя за TDesktop с публичным api_id (gifts-tracker), — рискованная практика, не повторяем.
8. **Комиссии противоречивы** (`MARKETS.md` §6). До проверки владельцем net — только «оценка».
9. **Малварь в экосистеме.** Раздел I и icfpztaorrmf — типичные приманки (exe + логин в Telegram / ключ кошелька). Ничего не скачивали.
10. **Антипримеры исполнения** (morgan): подпись присланных сервером транзакций без проверки адресатов/сумм, мнемоника открытым текстом. В `execution/` так не делаем.

## 5. Что осталось открытым после Этапа 0

- **Живые форматы ответов** (Этап 2, запись фикстур через Telethon-сессию владельца, только чтение, после согласования списка запросов).
- **Бот и short_name Mini App Tonnel** для `requestAppWebView` — в коде не найдено; нужно у владельца или на живом шаге.
- **soft/hard баланс MRKT** — в коде не объяснено.
- **Комиссии** — проверка владельцем (условие Этапа 7).
- **gifts-buyer** и **watchflowguide** — репозитории недоступны.
- **UX закрытых сервисов (K)** — скриншоты владельца в `docs/research/ux/`.
