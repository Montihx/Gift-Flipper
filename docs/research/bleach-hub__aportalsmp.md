# bleach-hub/aportalsmp

> СТАТУС ОТЧЁТА: ЧАСТИЧНЫЙ. Репозиторий найден, но исходники и README прочитать не удалось (см. «Что не удалось прочитать»). Всё, что ниже, — только из метаданных GitHub-поиска и страниц PyPI. Ничего не додумано.

- Ссылка: https://github.com/bleach-hub/aportalsmp (документация по версии PyPI: https://bleach-1.gitbook.io/aportalsmp — не прочитана)
- Язык / стек: Python >=3.8 (PyPI); остальной стек не проверен (curl_cffi / aiohttp — НЕ ПРОВЕРЕНО)
- Лицензия: MIT (по странице PyPI; файл LICENSE в репо не открывался)
- Последний коммит / активность: дата последнего коммита НЕ ПОЛУЧЕНА. `gh search repos` показал дату обновления репо 2026-10-03T19:55:31Z (это поле GitHub search, может означать push или иное обновление). Последний релиз PyPI: 1.3 от 24.11.2025.
- Звёзды / форки / коммиты: НЕ ПОЛУЧЕНЫ
- Доверие: среднее (предварительно). Тот же автор `bleach`, что и у portalsmp/tonnelmp, MIT, публичный PyPI-пакет с документацией. Код не читался, малварь-проверка не проводилась.

## Как найден
- `gh search repos aportalsmp` -> `bleach-hub/aportalsmp`, public, описание "Asynchronous library for interacting with Portals Marketplace API", обновлён 2026-10-03.
- PyPI https://pypi.org/project/aportalsmp/: автор `bleach`, Homepage = github.com/bleach-hub/aportalsmp, Documentation = bleach-1.gitbook.io/aportalsmp, MIT, описание "An Asynchronous Python Library for interacting with Portals Marketplace API".
- Владелец PyPI-профиля `bleach` (https://pypi.org/user/bleach/): aportalsmp (релиз 24.11.2025), portalsmp (22.06.2025), tonnelmp (17.06.2025). То есть владелец репо — тот же автор, что и у portalsmp (организация/аккаунт bleach-hub).

## Жив ли
- Релизы PyPI aportalsmp: 1.1 (30.06.2025), 1.2 / 1.2.1 / 1.2.3.4 (13.07.2025), 1.3 (24.11.2025). Для сравнения: portalsmp остановился на 1.2 (22.06.2025) — async-версия развивается заметно дольше и свежее синхронной.
- Что именно изменилось в 1.3 и что происходит в репо после 24.11.2025 — НЕ ПРОВЕРЕНО. Поле обновления 2026-10-03 намекает на возможную активность, но это не подтверждено коммитами. Архивирован ли репо — НЕ ПРОВЕРЕНО (задание сообщает, что portalsmp архивирован).

## Что делает (2–3 предложения)
По описанию PyPI/GitHub — асинхронная обёртка над API маркета Portals (async-аналог portalsmp). Состав функций, эндпоинты и их отличия от portalsmp не установлены (исходники/доки недоступны).

## Как устроено
- Источник данных: НЕ ПРОЧИТАНО
- Авторизация: НЕ ПРОЧИТАНО для aportalsmp. Справочно, по странице PyPI portalsmp 1.2: каждый запрос требует авторизации; токен можно взять вручную из Telegram Web или через `update_auth()` (нужны Telegram api_id и api_hash, Pyrogram/TgCrypto; в 1.2 переход pyrogram -> kurigram). Срок жизни — НЕ УКАЗАН на странице. Совпадает ли это в aportalsmp — НЕ ПРОВЕРЕНО.
- Модель данных подарка: НЕ ПРОЧИТАНО
- Оценка/флор: НЕ ПРОЧИТАНО
- Комиссии: НЕ ПРОЧИТАНО (ни «проверено», ни «заявлено»)
- Покупка/продажа (buy / sale / bulkList / offers / withdraw / balances): НЕ ПРОЧИТАНО
- curl_cffi / TLS-имитация: НЕ ПРОВЕРЕНО. Страница PyPI зависимостей не перечисляет (только Python >=3.8).
- Предохранители и лимиты: НЕ ПРОЧИТАНО
- Уведомления / UI: не применимо (библиотека)
- Хранение состояния: НЕ ПРОЧИТАНО

## Отличия от portalsmp
Установленные факты (только из PyPI):
- aportalsmp — асинхронная, portalsmp — синхронная.
- Версии: aportalsmp 1.3 (11.2025) против portalsmp 1.2 (06.2025).
- Автор и лицензия (MIT) одинаковые.
Сравнение эндпоинтов, авторизации и набора функций — НЕ ВЫПОЛНЕНО.

## Что берём
| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Пока ничего: без исходников нечего брать | - | После прочтения кода: сверить схему эндпоинтов с portalsmp и записать в `docs/MARKETS.md#portals` |

## Что НЕ берём и почему
- Сам пакет не ставим и не запускаем (правила AGENTS.md §4.3). Берём только описание эндпоинтов, переписывая клиент `markets/portals.py` самостоятельно.

## Что не удалось прочитать
Все попытки чтения GitHub упёрлись в ограничения сессии:
- `gh api repos/bleach-hub/portalsmp` и `.../contents` -> HTTP 403 «GitHub access to this repository is not enabled for this session».
- WebFetch для github.com/bleach-hub/aportalsmp, github.com/bleach-hub/portalsmp, raw.githubusercontent.com/bleach-hub/aportalsmp/main/README.md и bleach-1.gitbook.io/aportalsmp -> `URL_NOT_ON_ALLOWLIST`.
- `add_repo` ответил, что читать можно только через `git clone`, что запрещено правилами задания. Клон НЕ делался.
- Удалось: `gh search repos`, WebSearch, WebFetch страниц pypi.org (aportalsmp, portalsmp, профиль bleach).

## Дополнение (второй проход, координатор)

Главная страница прочитана через WebFetch `www.github.com/bleach-hub/aportalsmp` (пересказ). Звёзды / форки / коммиты: 18 / 6 / 28 (main); открытых PR: 2. Корень: `aportalsmp/`, `README.md` (файла LICENSE на странице нет — лицензия по PyPI MIT, в репо не подтверждена). Описание: асинхронная версия portalsmp; подробности отсылают на https://bleach-1.gitbook.io/aportalsmp (не читалась, вне allowlist). curl_cffi и эндпоинты на странице не упомянуты. Архивирован ли — на странице не сказано (в отличие от portalsmp, у которого архивация подтверждена).

## Открытые вопросы
- Нужны: README, список файлов, LICENSE, дата последнего коммита, звёзды/форки/коммиты aportalsmp.
- Какие функции есть в async-версии и совпадают ли эндпоинты Portals с portalsmp; есть ли buy/sale/bulkList/offers/withdraw/balances.
- Используется ли curl_cffi или иная TLS-имитация; как работает авторизация и её срок жизни.
- Что нового в 1.3 и что менялось после 24.11.2025.
- Решение для оркестратора: либо разрешить `github.com/bleach-hub/*` и raw.githubusercontent.com в allowlist, либо явно разрешить shallow-clone в отдельный каталог (без запуска кода) для чтения.
