# pypi: tgmrkt-api

> Источник: метаданные PyPI JSON `https://pypi.org/pypi/tgmrkt-api/json`, получены 2026-11-09 (`curl`, HTTP 200). Сам пакет (wheel/sdist) НЕ скачивался и не устанавливался, исходники не читались. Всё ниже — из полей JSON и long_description (README пакета на PyPI). Ранее использованные данные piwheels оставлены только там, где они сверяются.

- Ссылка: https://pypi.org/project/tgmrkt-api/
- Язык / стек: Python, `requires_python >=3.7`, зависимость только `requests>=2.28.0` (синхронный) — из PyPI JSON
- Лицензия: поле `license` пустое; классификатор `License :: OSI Approved :: MIT License`; в README пакета «MIT License - Смотри файл LICENSE» — из PyPI JSON
- Последний релиз / активность: единственная версия 0.1.0, загружена 2025-11-04T08:48:35Z (wheel) и 08:48:37Z (sdist); не yanked; `vulnerabilities: []` — из PyPI JSON
- Звёзды / форки / коммиты: н/д — репозиторий исходников не указан (`home_page` = null, `project_urls` = null)
- Автор: `Nsvl`, e-mail не указан, maintainer не указан — из PyPI JSON
- Доверие: НИЗКОЕ / НЕ ПРОВЕРЕНО (нет репозитория, исходники не читались)

## Метаданные

| Поле | Значение | Источник |
|---|---|---|
| Версия | 0.1.0 (единственная) | PyPI JSON |
| summary | "Python wrapper for TG MRKT API - Telegram marketplace for gifts and stickers trading" | PyPI JSON |
| keywords | telegram tgmrkt nft gifts stickers marketplace trading api | PyPI JSON |
| Файлы | `tgmrkt_api-0.1.0-py3-none-any.whl` 9766 байт, sha256 `8083c6e545ce8be0bcae7ab78b4ed7c7e50a416356b1b709f5845493e1f1f555`; `tgmrkt_api-0.1.0.tar.gz` 12656 байт, sha256 `c667a27e38293a38e4bb320e4c3fbe540cd33834147539f6b39eecb9c0190123` | PyPI JSON |
| Сверка с piwheels | в прежней версии отчёта был wheel 9729 байт, sha256 `ddd29ee0…` с piwheels — это другой файл (piwheels собирает свои колёса из sdist), с PyPI не совпадает; для проверки целостности опираться на хэши PyPI | PyPI JSON vs прежний отчёт |
| Имя модуля | `mrkt_api` (`from mrkt_api import ...`) — отличается от имени дистрибутива `tgmrkt-api` | README пакета |
| Ссылки в README | `https://tgmrkt.io`, `https://pypi.org/project/mrkt-api` (другое имя пакета!) | README пакета |

## Что делает (2–3 предложения)

По README — синхронная обёртка над API MRKT только для чтения: поиск подарков с фильтрами, полный парсинг коллекции с автоматической пагинацией, статистика цен по коллекции (floor/ceil/avg/median), мониторинг флоров с логом в JSON, экспорт в CSV. Покупки и продажи нет: «Поддерживает только поиск/просмотр подарков (покупка/продажа еще нет)».

## Как устроено (только из README пакета на PyPI)

- Источник данных / эндпоинты: **пути и HTTP-методы в README не указаны**. Функции: `search_gifts(auth, model_names=[...], count=20)`, `my_gifts(auth, count=20)`, `get_all_gift_names`, `parse_collection_full(auth, "Ice Cream", max_pages=...)`, `get_collection_stats`, `get_top_floors`, `get_collection_floor`, `get_collection_floors_from_saling` (имя намекает на `gifts/saling`), `monitor_floors(..., interval_sec=300, ...)`, `export_to_csv`, `export_collection_floors`, `get_competitions`, `get_stars_gifts`, `get_sticker_collections`, `nano_to_ton`.
- Авторизация: токен вручную из DevTools — открыть `tgmrkt.io` в браузере, вкладка Network, взять заголовок запроса к `api.tgmrkt.io` `Authorization: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (по шаблону — формат UUID). Получения через `initData` нет. При истечении — ошибка «Auth expired», «получи новый из DevTools». Срок жизни не указан.
- Модель подарка: README показывает уже преобразованный обёрткой словарь (не сырой ответ API): `name` ('IceCream-12345'), `number`, `title`, `model`, `backdrop`, `symbol`, `price_ton` (1.254), `price_nano` (1254000000), `model_rarity`/`backdrop_rarity`/`symbol_rarity` (per mille), `total_rarity`, `gift_type` ('Upgraded'), `id` (uuid).
- Единицы цен: пример `price_nano: 1254000000` ↔ `price_ton: 1.254` и `nano_to_ton(1_000_000_000) → 1.0` — согласуется с nanoTON в amrkt. Сырой ответ API не показан.
- Оценка/флор: floor = минимальная цена среди листингов `saling`, плюс ceil/avg/median по просканированным страницам (`max_pages`). Деталей нет.
- Комиссии: не упоминаются.
- Покупка/продажа: нет (по словам автора).
- Пагинация: «Автоматическая обработка пагинации», параметр `max_pages`; размер страницы в примерах `count=20`.
- Лимиты: «API не имеет задокументированных лимитов», совет — интервалы мониторинга 300+ с.
- Заголовки Referer/Origin, TLS-имитация: в README не упоминаются; зависимость только `requests` (без `curl_cffi`), значит TLS-отпечаток браузера, вероятно, не имитируется — вывод из списка зависимостей, код не читался.
- Хранение: логи мониторинга в JSON-файл, экспорт в CSV.

## Признаки подозрительности

- Нет ссылки на репозиторий; проверить код можно только скачав пакет, что запрещено правилами.
- Имя дистрибутива (`tgmrkt-api`), имя модуля (`mrkt_api`) и ссылка на PyPI в README (`mrkt-api`) не совпадают — признак небрежной упаковки или переименования; возможна путаница с другими MRKT-пакетами (`amrkt`, `mrkts`).
- Один релиз, автор с ником без e-mail, лицензия только классификатором.
- Признаков вредоносности в метаданных нет (зависимость одна — `requests`, ссылок на сторонние хосты кроме `tgmrkt.io` и PyPI нет), но содержимое пакета не проверялось.

## Что берём

| Что | Куда у нас | Как |
|---|---|---|
| Подтверждение: цены в nanoTON, токен в `Authorization` (формат похож на UUID) | `docs/MARKETS.md#mrkt` | Как косвенное подтверждение к amrkt/boostNT, не как первоисточник |
| Идея: статистика floor/median по листингам коллекции, мониторинг с интервалом ≥ 300 с | `pricing/floor.py` | Идея, переписать |
| Наблюдение: у MRKT есть веб-версия `tgmrkt.io`, откуда можно снять токен в DevTools | ручная отладка | Только для ручной проверки, не для продакшена |

## Что НЕ берём и почему

- Сам пакет: `pip install` запрещён (AGENTS.md §4.3), исходники не проверены, репозитория нет.
- Ручное получение токена из DevTools — у нас токен получается автоматически через `initData` (Telethon).
- Синхронный `requests` без TLS-имитации — не подходит для нашего асинхронного клиента.

## Открытые вопросы

- Какие именно пути API вызываются (`gifts/saling`? что за эндпоинты «competitions», «stars gifts», «sticker collections»?) — без чтения исходников не установить. Можно было бы посмотреть как текст через inspector PyPI, если это разрешат.
- Действительно ли токен MRKT имеет формат UUID (по README пакета) — сверить с ответом `/auth`.
- Связь с пакетом `mrkt-api` на PyPI (ссылка из README) — не проверялась.

## Для MARKETS.md

- Токен MRKT передаётся в заголовке `Authorization`, по шаблону README пакета имеет вид UUID `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` — из README пакета на PyPI (не проверено).
- Цены — nanoTON (`1254000000` = 1.254 TON) — из README пакета на PyPI (преобразованный объект обёртки, не сырой ответ).
- Существует веб-версия `https://tgmrkt.io` — из README пакета на PyPI.
- Эндпоинты, методы, тела: в README пакета не указаны.
