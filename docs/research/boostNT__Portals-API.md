# boostNT/Portals-API

Источник: исходники, клон от 2026-11-09, коммит `488e6e8a3b85b00849d847cf6da466d1a77a49ea` (2026-02-07). В репозитории один файл — `README.md` (177 строк); прочитан дословно как текст, плюс история `git log -p`. Ничего не запускалось. Ссылки `README:N` — на строки этого файла.

- Ссылка: https://github.com/boostNT/Portals-API
- Язык / стек: только документация на русском; примеры на Python (Pyrogram raw API, `curl_cffi.requests`).
- Лицензия: файла лицензии нет (в клоне только README). Код примеров не копируем, берём описание API.
- Последний коммит / активность: 2026-02-07 (удалена строка с контактом автора). Последнее содержательное обновление — 2025-11-06 (коммит 5340371 «Updated domain and filter by gift name»). Первый коммит — 2025-05-31.
- Звёзды / форки / коммиты: звёзды и форки не установлены; коммитов 13 (полная история).
- Доверие: среднее. Это короткая неофициальная документация без кода-пакета: ни бинарников, ни ссылок на скачивание, ни обфускации. В примерах `api_id`/`api_hash` — явные заглушки (в отчёт не переносим). Покупка, листинг, баланс не описаны. Плюс: обновлялась в ноябре 2025, позже portalsmp (июнь 2025).

## Что делает (2–3 предложения)

Описывает, как читать каталог маркета Portals: `GET /api/nfts/search` с фильтрами и сортировками, `GET /api/collections?search=` для получения UUID коллекции, и как получить заголовок `Authorization: tma …` через Pyrogram (`RequestAppWebView`) или вручную из DevTools Telegram Web. Сделок (buy/sell), баланса, офферов, комиссий нет.

## Как устроено

### Базовый URL

- Текущая версия README: `https://portal-market.com` (без «s»), API — `https://portal-market.com/api` (README:9, 36, 113).
- История домена по `git log -p` (из README, разные версии): `market.portals.tg` (2025-05-31, b303e98) → `portals-market.com` (2025-06-02…06-03) → `portal-market.com` (2025-11-06, 5340371).

### Эндпоинты (из README)

| Метод | Путь | Параметры | Что читается из ответа |
|---|---|---|---|
| GET | `/api/nfts/search` | см. таблицу фильтров; пример `?offset=0&limit=20&sort_by=price+desc&status=listed` (README:36) | `['results']` (README:125, 136) |
| GET | `/api/collections?search={name}&limit=10` | `search` — название коллекции | UUID в `['collections'][0]['id']` (README:43-45, 146-148) |

Фильтры `/api/nfts/search` (README:15-26):

| Параметр | По README |
|---|---|
| `collection_ids` | UUID коллекций через запятую (с 2025-11-06; до этого в README был `filter_by_collections` — названия через запятую) |
| `filter_by_models` | модели через запятую |
| `filter_by_backdrops` | фоны через запятую |
| `external_collection_number` | число, поиск по вхождению в номер |
| `exclude_bundled` | True/False — исключить лоты в бандлах (добавлено 2025-11-06) |
| `premarket_status` | `all` / `only_premarket` / `without_premarket` (добавлено 2025-11-06) |
| `min_price`, `max_price` | мин./макс. цена, единицы и формат не указаны |
| `limit` | максимум 100 |
| `offset` | смещение |
| `status` | `listed` / `unlisted`; без параметра — все |
| `sort_by` | `listed_at` (только `desc`), `price`, `external_collection_number`, `model_rarity` + `asc`/`desc`; в URL `price+desc` |

Ответ: описан только верхний ключ `results` / `collections`; поля объекта подарка в README нет.

### Авторизация (README:51-97, 155-170)

- `client.get_users('portals')` → `InputUser(user_id, access_hash=bot_entity.raw.access_hash)`; `client.resolve_peer('portals')`; `InputBotAppShortName(bot_id=bot, short_name='market')`; `client.invoke(RequestAppWebView(peer=peer, app=bot_app, platform="android"))`.
- `init_data = unquote(web_view.url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion', 1)[0])`; `token = f'tma {init_data}'`; заголовок `{'Authorization': token}`.
- Ручной способ: Telegram Web → DevTools → Network → любой запрос к `portal-market.com` → заголовок `Authorization` (README:91).
- Срок жизни: «неизвестно, но точно более суток» (README:97).
- Другие заголовки (Origin/Referer/UA) в примерах не задаются; запросы через `curl_cffi` с `impersonate='chrome'` (README:123, 134, 146; добавлено 2025-11-06, до этого обычные запросы без имперсонации).

### Остальное

Модель данных подарка, флоры, комиссии, покупка/продажа, ошибки, лимиты запросов, WebSocket — в README отсутствуют.

## Сверка с bleach-hub/portalsmp (код, коммит 77fb217, июнь 2025)

| Пункт | boostNT README (ноябрь 2025) | portalsmp (код) | Оценка |
|---|---|---|---|
| Домен | `portal-market.com` | `portals-market.com` (portalsapi.py:65, а также Origin/Referer 72-73) | **Расхождение.** В июне 2025 boostNT тоже писал `portals-market.com`; смена домена произошла после того, как portalsmp заброшен. Актуальность проверить живым запросом |
| Фильтр по коллекции | `collection_ids` = UUID | `filter_by_collections` = название (Title Case) (portalsapi.py:124-126) | **Расхождение.** До 2025-11-06 boostNT описывал `filter_by_collections` по названию — совпадало с portalsmp |
| `filter_by_models`, `filter_by_backdrops` | есть | есть | совпадает |
| `filter_by_symbols` | нет | есть (143-149) | только в portalsmp |
| `exclude_bundled`, `premarket_status`, `external_collection_number` (фильтр) | есть | нет | только в boostNT (новее) |
| `sort_by` | `listed_at desc`, `price`, `external_collection_number`, `model_rarity` | те же 4 поля (55-63) | совпадает |
| Максимум `limit` | 100 | «probably max is 20» (докстринг, 86) | **Расхождение**, проверить |
| `status` | listed/unlisted/не указывать | всегда `status=listed` в search (151) | совместимо |
| Ключ ответа поиска | `results` | `results` (159) | совпадает |
| Бот / short_name | `portals` / `market` | `portals` / `market` (40, 44) | совпадает |
| Метод | `messages.RequestAppWebView` | `messages.RequestAppWebView` (45-51) | совпадает |
| `platform` | `"android"` | `"desktop"` (49) | различие; влияние на токен неизвестно |
| Получение access_hash бота | `client.get_users()` → `.raw.access_hash` | raw `users.GetUsers` (41-43) | эквивалентно |
| Выделение initData | `tgWebAppData=` … `&tgWebAppVersion`, `unquote`, `tma ` | то же (52-53) | совпадает |
| TLS | `impersonate='chrome'` | `impersonate="chrome110"` + свой UA/Origin/Referer | различие в деталях |
| Срок токена | «более суток» | README portalsmp: «вероятно 1–7 дней» для Telegram Web | оценки авторов, не проверено |
| Эндпоинт коллекций | `GET /api/collections?search=&limit=` → `collections[0].id` | `GET collections?limit=` → `collections` (без `search`) | совместимо; `search` только в boostNT |
| Покупка / листинг / баланс / офферы | нет | есть (см. отчёт portalsmp) | только portalsmp |

## Что берём

| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Актуальный (на ноябрь 2025) домен `portal-market.com` | `docs/MARKETS.md#portals`, настройка в `markets/portals.py` | Домен — параметр конфигурации; при старте проверять оба |
| Фильтр `collection_ids` (UUID) + `GET /api/collections?search=` для имя → UUID | `markets/portals.py`, `pricing/aliases.py` | Кэш маппинга из ответа `collections`, не статичный словарь |
| `exclude_bundled`, `premarket_status`, `limit ≤ 100` | `markets/portals.py` | Для флипа: `exclude_bundled=true`, `premarket_status=without_premarket` (проверить) |
| Схема `tma`-токена (совпадает с portalsmp) | `markets/portals.py` (Telethon) | Переписать; при 401/403 перевыпускать |

## Что НЕ берём и почему

- Код примеров (нет лицензии) — только описание API.
- Ручной вариант с копированием токена из DevTools — не подходит для автоматического сервиса.
- Всё про сделки и баланс — здесь не описано; источник — portalsmp.

## Открытые вопросы

- Какой домен живой сейчас (ноябрь 2026): `portal-market.com` или `portals-market.com`; нужны ли новые Origin/Referer.
- Принимается ли ещё `filter_by_collections` по названию.
- Реальный максимум `limit`.
- Формат и единицы `min_price`/`max_price` (portalsmp шлёт целые числа).
- Поля объекта подарка в новой версии API (README их не даёт; есть только пример из README portalsmp, июнь 2025).
- Срок жизни токена, лимиты запросов, поведение на 429.

## Для MARKETS.md

- Домен API по boostNT (2025-11-06): `https://portal-market.com/api` (из README:113). Расхождение с portalsmp: `https://portals-market.com/api/` (из кода portalsmp, portalsapi.py:65). История: `market.portals.tg` → `portals-market.com` → `portal-market.com` (из истории README).
- `GET /api/nfts/search?offset&limit(≤100)&sort_by=<field>+<asc|desc>&status=listed|unlisted&collection_ids=<uuid,…>&filter_by_models&filter_by_backdrops&external_collection_number&exclude_bundled=True|False&premarket_status=all|only_premarket|without_premarket&min_price&max_price` → `results[]` (из README:15-36).
- `sort_by`: `listed_at` (только desc), `price`, `external_collection_number`, `model_rarity` (из README:28-33).
- `GET /api/collections?search=<name>&limit=10` → `collections[0].id` = UUID коллекции (из README:43-45).
- Авторизация: `Authorization: tma <unquote(tgWebAppData)>` из `messages.requestAppWebView(peer=@portals, app=InputBotAppShortName(@portals, "market"), platform="android")` (из README:65-80). Совпадает с portalsmp, кроме `platform` (там `desktop`).
- TLS: `curl_cffi` `impersonate='chrome'` (из README:123).
- Срок токена: «более суток», точно неизвестно (из README:97).
