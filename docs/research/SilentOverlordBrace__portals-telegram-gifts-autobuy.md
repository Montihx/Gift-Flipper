# SilentOverlordBrace/portals-telegram-gifts-autobuy

> Источник: только текст README (raw, ветка main), скачан координатором 2026-11-09. Refs по данным координатора: `main` + тег `v2.4.11`. Репозиторий НЕ клонировался, ссылки из README НЕ открывались, релизы НЕ скачивались, ничего не запускалось. Все факты — «из README» (заявлены автором, не проверены). Старый отчёт (без доступа к README) заменён целиком; из него ничего не перенесено, кроме того, что метка «ПОДОЗРИТЕЛЬНО» теперь подтверждена текстом README.

- Ссылка: https://github.com/SilentOverlordBrace/portals-telegram-gifts-autobuy
- Язык / стек (из README): Python 3.11+, aiogram 3.x, Telethon, pydantic-settings, SQLite. Заявлено «Windows 10/11 only».
- Лицензия: README заявляет `MIT © 2026 SilentOverlordBrace` (свой ник). Файл LICENSE не читался.
- Последний коммит / активность: не установлено (клона нет). В README даты «проверено вживую 2026-10-28».
- Звёзды / форки / коммиты: не установлено.
- Доверие: **ПОДОЗРИТЕЛЬНО** — README — практически копия OnyxTarantulaLoop/portals-gifts-autobuy-bot (334 из 336 уникальных непустых строк общие), который распространяет `.exe` с обходом SmartScreen; здесь тот же необъяснимый «Windows-only companion runtime»; инструкция клонирования ведёт на **другой** репозиторий (`SilentOverlordBrace/portals-autobuy`); тег `v2.4.11` при статусе «alpha».

## Что делает (2–3 предложения)

По README — то же, что OnyxTarantulaLoop/portals-gifts-autobuy-bot: self-hosted снайпер подарков на Portals с кластерным флором, расчётом прибыли после комиссий, вторым мнением (оценка Telegram, флоры MRKT/Tonnel из локальных файлов), карточками в админ-бота и покупкой в ограниченном живом режиме. По умолчанию — практика.

## Как устроено (по README, не проверено)

Текст разделов «How it works», «Configuration», «Safety», «Before going live» **дословно совпадает** с README OnyxTarantulaLoop. Кратко:
- Polling каждые 2 с: «самые новые» по всем коллекциям + «самые дешёвые» на фильтр правила; флоры кэшируются 60 с; бандлы исключены в поиске.
- Поиск и флоры Portals публичные; покупка и баланс — через `initData` Mini App @portals, полученный Telethon-сессией (или вручную `PORTALS_INIT_DATA`).
- Покупка `POST /nfts` с `{"nft_details":[{"id","price":"<строка>"}]}`; успех — только явный, иначе «result unknown». Никогда не продаёт.
- SQLite + `data/events.jsonl` + обменный файл флоров `data/floors_portals.json`.

## Идеи по пунктам задания I (только идеи)

Содержимое совпадает с отчётом `docs/research/OnyxTarantulaLoop__portals-gifts-autobuy-bot.md`; ниже — сжатая версия.

1. **Кластерный флор:** самая низкая цена с ≥2 другими предложениями в пределах +10% выше (кластер ≥3). Доверие `high/med/low` по числу сопоставимых; без кластера — `low`; по умолчанию `min_confidence=med`. Скачок флора >25% за час понижает уровень. Запасной путь: медиана 3 самых дешёвых других (метка `thin`, `low`) → флор модели → символа → коллекции. Ловушки: бандлы, `unlocks_at` в будущем, цена <25% флора, неизвестная единица цены.
2. **Оценка Telegram** (`payments.getUniqueStarGiftValueInfo`): берутся average, last sale, listed count; выше средней **и** последней продажи при `low`-флоре → спросить. Автор отмечает, что «same type» в документации не определён. Поля метода сверены отдельно — `SUMMARY.md` §3.
3. **Предохранители:** `DRY_RUN=true` — жёсткий замок; live требует `DRY_RUN=false` + `/dry off`; кнопка «Go live for 24 h» одноразовая, 10 мин, только если все правила `ready`; live-окно `LIVE_ARM_HOURS=24`. Лимиты на all-in под одним локом: `MAX_PRICE_TON=10`, `DAILY_BUDGET_TON=30` (скользящие 24 ч), `MAX_BUYS_PER_HOUR=3`, `CONFIRM_ABOVE_TON`; NaN/inf запрещены, fail closed. Брейкеры: обвал флора > `CRASH_PCT`/ч, `LOSS_STREAK_N` убытков подряд, расхождение баланса > трат + допуск, `AUTO_PAUSE_ERRORS` ошибок покупки подряд. `/panic` — пауза + практика + протухание карточек; снятие `/resume` (одноразовое подтверждение) + новый `/dry off`. Живая покупка пишется как «result unknown» до отправки и учитывается в лимитах. Shadow-правила.
4. **Режимы** `auto/confirm/watch` на правило; даже `auto` спрашивает при: «слишком хорошо», блокировке, **дешевле на другом маркете**, цене выше оценки Telegram на `low`-флоре, стоимости > `CONFIRM_ABOVE_TON`. Перепроверка цены перед тапом, карточка живёт 90 с, двойной тап безопасен.
5. **`/doctor`:** конфиг, Telegram-сессия, 2FA, права файла сессии, авторизация Portals, доступность, сдвиг часов, движок, правила, комиссии, пиры, БД, лимиты; подсказка на каждую ошибку; exit code 1.
6. **Комиссии — заявлено, не проверено:** Portals покупка 0%, продажа 5% (0% для `zero_commission`), вывод 0.1 TON; `FEES_VERIFIED=false` по умолчанию.

## Признаки малвари / накрутки

| Признак | Результат (из README) |
|---|---|
| Ссылки на `.exe` / `.zip` / релизы | В README ветки main прямой ссылки на скачивание **нет** (в отличие от Onyx, где блок Download с `.exe`). README тега `v2.4.11` координатором не передан — не проверено. Релизы не открывались. |
| «Windows-only companion runtime» | **Да:** «The CLI refuses to start anywhere else… because the packaged companion runtime is a Windows program». Для Python-бота на aiogram/Telethon необъяснимо; та же фраза во всех четырёх README семейства, и в одном из них (Onyx) рядом лежит `.exe`. Сильный признак скрытого бинарника в пакете. |
| Ссылка клонирования на другой репо | **Да:** `git clone https://github.com/SilentOverlordBrace/portals-autobuy.git`, а сам репозиторий — `portals-telegram-gifts-autobuy`. Пользователь, следующий инструкции, получит другой код. |
| Несоответствие версий | Тег `v2.4.11` (по данным координатора) при «Status: alpha» и «buy… never run with a real account». |
| Внешние домены | github.com, img.shields.io (статичные бейджи), t.me, my.telegram.org, www.python.org, console.anthropic.com; в тексте — `portal-market.com`, `tonapi.io`. Файлообменников нет. |
| Seed-фраза / приватный ключ | Не запрашиваются. |
| Сессия Telegram | `login` просит телефон, код, 2FA и хранит Telethon-сессию локально; вместе с подозрением на бинарник — вектор кражи аккаунта и баланса Portals. |
| Автозапуск | `schtasks /Create ... /SC ONLOGON`. |
| Шаблонность | С Onyx — 334 из 336 уникальных непустых строк общие (отличаются только блок Download и ник в URL). С MRKT-версией (smashguidetram) — 165 общих строк, с Tonnel (Townkibarrier) — 143. Фраза «Replace `SilentOverlordBrace` with the GitHub account that hosts this repository» — шаблон для перезалива. |
| Лицензия на другой ник | Здесь — на свой ник; но **этот же ник** стоит в лицензии README Onyx, то есть оба аккаунта — одно семейство. |
| Обещания прибыли | Явных нет, есть дисклеймер. |
| base64 / обфускация в README | Нет. |

**Вывод доверия: ПОДОЗРИТЕЛЬНО.** Текст — общий шаблон семейства, распространяющего неподписанный `.exe`; инструкция ведёт в другой репозиторий; заявлен «Windows-компаньон», которому в таком стеке нечего делать. Код и релизы не трогать.

## Что берём

То же, что из OnyxTarantulaLoop (см. его отчёт): кластерный флор с доверием и запасным путём → `pricing/floor.py`; net-прибыль и `FEES_VERIFIED` → `pricing/fees.py`; оценка Telegram как второе мнение → `pricing/tg_value.py`; DRY_RUN-замок, live-окно 24 ч, лимиты, брейкеры, `/panic`, запись `unknown` до запроса → `execution/`; режимы и ask-first → `rules/`, `bot/`; `/doctor` → `bot/`. Только как идеи, всё переписываем.

## Что НЕ берём и почему

Код, `requirements.txt`, релизы — подозрительный источник (AGENTS.md §4.3). Цифры комиссий и формат ответов — не принимать на веру.

## Открытые вопросы

- Отличается ли README тега `v2.4.11` от main (не передан).
- Существует ли `SilentOverlordBrace/portals-autobuy`, на который ведёт clone — не проверяли (ссылки не открываем).
- Поля `getUniqueStarGiftValueInfo` — см. `SUMMARY.md` §3.

## Для MARKETS.md

Идентично разделу «Для MARKETS.md» в `OnyxTarantulaLoop__portals-gifts-autobuy-bot.md` (тот же текст README): `portal-market.com`; `GET /nfts/search`, `/collections?limit=500`, `/collections/filters`, `/collections/floors` — публичные; `GET /users/wallets/` 401 без авторизации; `POST /nfts` с `{"nft_details":[{"id","price":"<строка>"}]}`; `x-ratelimit-limit: 2` (search) / `12` (floors), 1.5 rps; Mini App short name `market`; комиссии 0% / 5% / 0.1 TON. Всё — **из README подозрительного репо, не проверено**.
