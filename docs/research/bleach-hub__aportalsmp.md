# bleach-hub/aportalsmp

> Источник: исходники, клон от 2026-11-09, коммит `d1daafdb81818a2964dc442e1e96142cee1c8fc8`. Код только прочитан как текст, ничего не запускалось. Живых запросов к API не было: все пометки ниже — «из кода (файл:строка)» или «из README». Пути файлов даны относительно корня репозитория.

- Ссылка: https://github.com/bleach-hub/aportalsmp (README отсылает к документации https://bleach-1.gitbook.io/aportalsmp, она не читалась)
- Язык / стек: Python, asyncio. HTTP: `curl_cffi.requests.AsyncSession` с `impersonate="chrome110"` (`aportalsmp/handlers.py:4,31`). Авторизация через `pyrogram` (`aportalsmp/auth.py:1-4`). Файлов зависимостей (`setup.py`, `pyproject.toml`, `requirements.txt`) в репо нет, поэтому версии и выбор пакета (pyrogram или kurigram, который ставит модуль `pyrogram`) в коде не установлены.
- Лицензия: **в репозитории лицензии нет.** Файла LICENSE, `pyproject.toml` и `setup.py` нет, README лицензию не упоминает. По метаданным PyPI (из прошлой версии отчёта) заявлена MIT, но в самом репо это не подтверждено. Решение владельца (2026-11-09, D-013): отсутствие файла LICENSE не считать запретом; aportalsmp — основной источник по Portals, фрагменты кода можно переносить с указанием источника (MIT по метаданным PyPI). Как зависимость не ставим (D-007).
- Последний коммит / активность: 2025-11-30 (`d1daafd`, «Update collections_ids.py», автор into-the-null). Последнее изменение кода: 2025-11-24 (PR #6 proxy, PR #7 buy response, автор Arseny). Автор `bleach` сам последний раз коммитил 2025-09-14 (merge PR #1). С конца ноября 2025 до 2026-11-09 (≈11 месяцев) коммитов нет. Проект **малоактивен / фактически заброшен**: последние правки внесены сторонними контрибьюторами. Архивирован ли репо, по клону установить нельзя.
- Звёзды / форки / коммиты: звёзды и форки не установлены. Коммитов 28 (полная история: клон глубиной 50, история короче). Первый коммит: 2025-06-26.
- Доверие: **среднее**. Малвари не найдено: нет `exec`/`eval`/base64, сеть идёт только на `portal-market.com`, сессия Telegram никуда не отправляется (только локальный файл pyrogram в `session_path`). В README есть адреса для донатов (TON/TRC20), это нормально. Проблемы качества: нет ретраев и обработки 429, голый `except:`, нет файла зависимостей, нет лицензии.

## Что делает (2–3 предложения)
Асинхронная обёртка над приватным REST API маркета Portals (`https://portal-market.com/api/`). Покрывает поиск листингов, флоры (по коллекциям и по модели/фону/символу), активность маркета, покупку, листинг и смену цены, офферы на подарок и на коллекцию, баланс и вывод TON, а также функции, которых нет в синхронном portalsmp: розыгрыши, передача и вывод подарков, статистика профиля. Авторизация: строка `tma <initData>` в заголовке `Authorization`, initData берётся через Pyrogram из mini-app бота `@portals`.

## Как устроено

### Базовый URL и общие заголовки
- `API_URL = "https://portal-market.com/api/"` — из кода (`aportalsmp/utils/other.py:11`). До коммита `a375464` (2025-11-06, «Update url») было `https://portals-market.com/api/`. В синхронном portalsmp так и осталось `portals-market.com` (`portalsmp/portalsapi.py:65` в клоне bleach-hub__portalsmp). **Актуальный домен — `portal-market.com`** (без «s»): это самая свежая правка, и она совпадает с boostNT/Portals-API.
- Все запросы отправляют один набор заголовков `HEADERS_MAIN` и дописывают к нему `Authorization` — из кода (`aportalsmp/utils/other.py:13-21`):
  ```
  Authorization: <authData>              # "tma <initData>"
  Accept: application/json, text/plain, */*
  Accept-Encoding: gzip, deflate, br, zstd
  Accept-Language: en-US,en;q=0.9,ru;q=0.8
  Origin: https://portal-market.com
  Referer: https://portal-market.com/
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ... Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0
  ```
  Отдельного `Content-Type` в коде нет: для POST и PATCH его ставит curl_cffi через `json=`. Заметка: TLS-отпечаток `chrome110` не совпадает с UA Edge 137. Работает ли это — из кода не узнать.
- **Каждая функция требует `authData`** и бросает `authDataError`, если он пустой, даже `search`, `giftsFloors` и `collections`. Нужна ли авторизация самому API для публичных маршрутов — в коде не установлено (проверка только на стороне библиотеки).

### HTTP-слой и ошибки (`aportalsmp/handlers.py`)
- `fetch(method, url, headers, json, timeout=15, impersonate="chrome110", proxies=None)` создаёт **новый `AsyncSession` на каждый запрос** (без переиспользования соединений) — из кода (`handlers.py:11-36`).
- Любое исключение при запросе (голый `except:`) превращается в `connectionError("Connection reset after {timeout} seconds…")` (`handlers.py:35-36`). Тип ошибки (таймаут, DNS, TLS) теряется.
- `requestExceptionHandler(response, func_name)` (`handlers.py:40-57`): если статус не 2xx, бросает `requestError` с текстом из `response.json()["message"]`, либо со всем JSON, либо с `response.text` (если текст длиннее 300 символов — «likely raw HTML»).
- **429, Retry-After, ретраев, backoff и throttle нет.** 429 — такая же `requestError`, как и любой не-2xx. В коде нет ни `sleep`, ни `retry`.
- Прокси (`proxies: dict`) принимает только `search()` (`gifts.py:122,224`; добавлено в коммите `ce97236`, 2025-11-24). Остальные функции прокси не пробрасывают.
- Иерархия исключений (`aportalsmp/classes/Exceptions.py`): `authDataError, offerError, accountError, requestError, connectionError, floorsError, giftsError, tradingError`. Все наследуют `Exception`.

### Авторизация (`aportalsmp/auth.py`)
- `async update_auth(api_id, api_hash, session_string="", session_path=os.getcwd(), session_name="account") -> str` (`auth.py:13`).
- Библиотека: **Pyrogram** (`from pyrogram import Client`, raw-функции `messages.RequestAppWebView`, `users.GetUsers`, типы `InputBotAppShortName`, `InputUser`; `auth.py:1-4`). Telethon не используется. Ставится ли форк kurigram — в репо не указано (нет файла зависимостей).
- Шаги — из кода (`auth.py:30-44`; ветка с `session_string`: `auth.py:46-60`, тот же код):
  1. `peer = await client.resolve_peer("portals")` — бот **`@portals`**.
  2. `GetUsers(id=[peer])` → `InputUser(user_id, access_hash)`.
  3. `InputBotAppShortName(bot_id=bot, short_name="market")` — **short_name `market`**.
  4. `RequestAppWebView(peer=peer, app=bot_app, platform="desktop")` — **platform `desktop`**. `start_param` и `write_allowed` не передаются.
  5. `initData = unquote(url.split('tgWebAppData=',1)[1].split('&tgWebAppVersion',1)[0])`: initData берётся из URL веб-вью, между `tgWebAppData=` и `&tgWebAppVersion`, и URL-декодируется.
  6. Возвращается `f"tma {initData}"` — эта строка целиком идёт в заголовок `Authorization`.
- Срок жизни токена в коде не указан. Автообновления нет: при 401 пользователь сам вызывает `update_auth()` ещё раз.
- Сессия pyrogram сохраняется файлом `<session_path>/<session_name>.session`. Наружу ничего не отправляется.

### Единицы цен
- **Цены в TON, десятичные, не nano.** Docstring `collectionOffer`: «Price in TON you want to offer» (`offers.py:138`). В примере ответа buy: `"price":"2.32"`, `"total_spent":"0"` (`gifts.py:535-550`).
- **В запросах цена передаётся строкой**: `str(price)` из `int|float` (`buy` — `gifts.py:567`; `sale` — `gifts.py:685`; `changePrice` — `gifts.py:611-613`; `makeOffer` — `offers.py:49`; `collectionOffer` — `offers.py:176`; `withdrawPortals` — `account.py:120-123`). В `editOffer` и `editCollectionOffer` — `str(float(x))` (`offers.py:120,215`). Округления и `Decimal` нет: `str(float)` может дать `"0.30000000000000004"`. У себя форматировать через `Decimal` с фиксированной точностью.
- **В ответах цены приходят строками**: объекты делают `float(data["price"])` (`classes/Objects.py:31-32`, `93-94`, `122-123`, `272-277`).
- Фильтр цены в `search` и `marketActivity`: `min_price`/`max_price` приводятся к `int` и добавляются в query, только если `max_price < 100000` (`gifts.py:162-169`, `262-269`). Дробные границы библиотека не поддерживает (на стороне API — не установлено).
- Минимум для `editOffer`/`editCollectionOffer` — 0.5 (проверка в библиотеке, `offers.py:114,209`).

### Таблица эндпоинтов (все — из кода; URL = `https://portal-market.com/api/` + путь)

| Функция (файл:строки) | Метод | Путь | Query / тело | Поля ответа (что читает библиотека) |
|---|---|---|---|---|
| `search` (`gifts.py:110-228`) | GET | `nfts/search` | query: `offset` int, `limit` int (по умолч. 20), `sort_by` (см. ниже), `min_price`, `max_price` int (только если max<100000), `collection_ids` — UUID коллекций через `,` (имя → UUID по локальной таблице `utils/collections_ids.py`), `filter_by_models`, `filter_by_backdrops`, `filter_by_symbols` — имена с заглавной буквы в каждом слове, `quote_plus`, список через `%2C`; всегда `status=listed`, `exclude_bundled=true\|false` (по умолч. true), `premarket_status=all\|only_premarket\|without_premarket` | `{"results": [PortalsGift…]}` |
| `giftsFloors` (`gifts.py:17-43`) | GET | `collections/floors` | — | `{"floorPrices": {<short_name>: <цена строкой/числом>}}` (`GiftsFloors.floor()` делает `float`) |
| `filterFloors` (`gifts.py:45-78`) | GET | `collections/filters` | query: `short_names=<short_name>` (`toShortName`: без пробелов, `'`, `’`, `-`, в нижнем регистре; `utils/functions.py:18-19`) | `{"floor_prices": {<short_name>: {"models": {name: price}, "backdrops": {...}, "symbols": {...}}}}` |
| `collections` (`gifts.py:80-106`) | GET | `collections` | query: `limit` (по умолч. 100) | `{"collections": [{id, name, short_name, photo_url, day_volume, volume, floor_price, supply}]}` (`Objects.py:327-361`) |
| `marketActivity` (`gifts.py:230-318`) | GET | `market/actions/` | query: `offset`, `limit`, `sort_by` (таблица SORTS; sort не проверяется → KeyError), `min_price`/`max_price`, `filter_by_collections` (**имена**, не UUID — старый стиль), `filter_by_models`, `filter_by_backdrops`, `filter_by_symbols`, `action_types` = `buy\|listing\|price_update\|offer` (список через `%2C`) | `{"actions": [{nft: PortalsGift, offer_id, type, amount, created_at}]}` (`Objects.py:363-388`) |
| `myActivity` (`gifts.py:451-478`) | GET | `users/actions/` | query: `offset`, `limit` | `{"actions": [{nft, target_user_id, nft_id, offer_id, type, amount, created_at, referrer_revenue, collection_id, metadata, offer: {status, price, recipient_id}}]}` (`Objects.py:390-447`) |
| `myPortalsGifts` (`gifts.py:418-449`) | GET | `nfts/owned` | query: `offset`, `limit`, `status=listed\|unlisted` | `{"nfts": [PortalsGift…]}` |
| `buy` (`gifts.py:525-580`) | POST | `nfts` | JSON: `{"nft_details": [{"id": "<nft uuid>", "price": "<TON строкой>"}]}` (в синхронной версии раньше был ещё `owner_id`, удалён) | Сырой JSON (с PR #7, 2025-11-24): `{total_requested, total_purchased, total_failed, total_spent: "str", purchase_results: [{id, status: "failed"/…, reason: "INSUFFICIENT_BALANCE"/…, price: "str", error_message}]}` — пример из docstring (`gifts.py:535-550`). **Важно: HTTP 2xx не значит, что покупка прошла — смотреть `total_purchased` и `purchase_results[].status`.** |
| `sale` (`gifts.py:658-697`) | POST | `nfts/bulk-list` | JSON: `{"nft_prices": [{"nft_id": "<uuid>", "price": "<TON строкой>"}]}` | `SaleResult`: `{successful_nfts: [...], failed_nfts: [...]}` (`Objects.py:449-462`) |
| `bulkList` (`gifts.py:622-656`) | POST | `nfts/bulk-list` | JSON: `{"nft_prices": nfts}` — список готовит вызывающий; хелпер `convertForListing(nft_id, price)` → `{"nft_id": id, "price": str(price)}` (`utils/functions.py:21-22`) | `SaleResult` (как у `sale`) |
| `changePrice` (`gifts.py:582-619`) | POST | `nfts/{nft_id}/list` | JSON: `{"price": "<TON строкой>"}` | Не читается, возвращается `None` (docstring: «likely a 204») |
| `withdrawGifts` (`gifts.py:699-734`) | POST | `nfts/withdraw` | JSON: `{"gift_ids": [uuid…]}` | Не читается (docstring: «[NOT TESTED]») |
| `transferGifts` (`gifts.py:480-521`) | POST | `nfts/transfer-gifts` | JSON: `{"nft_ids": [...], "recipient": "<username>", "anonymous": bool}` | Не читается |
| `myBalances` = balances (`account.py:64-89`) | GET | `users/wallets/` | — | `{balance, frozen_funds}` — строки, приводятся к float (`Objects.py:264-277`) |
| `withdrawPortals` = withdraw TON (`account.py:91-129`) | POST | `users/wallets/withdraw` | JSON: `{"amount": "<TON строкой>", "external_address": "<TON-адрес>"}` | `{"id": ...}` — ID вывода |
| `myPoints` (`account.py:10-35`) | GET | `points/me` (в синхронной версии — `points/my-points`) | — | `{total_points, summary: {purchase_points, sell_points, referral_points, bonus_points, purchase_count, sell_count, referral_count, bonus_count}}` |
| `myStats` (`account.py:37-62`) | GET | `users/profile/stats` | — | `{total_bought, total_sold, total_volume}` |
| `makeOffer` (`offers.py:14-60`) | POST | `offers` | JSON: `{"offer": {"nft_id": "<uuid>", "offer_price": "<str>", "expiration_days": 7}}` (`expiration_days` передаётся только при 7; 0 = без срока, поле не передаётся) | Не читается |
| `cancelOffer` (`offers.py:62-92`) | POST | `offers/{offer_id}/cancel` | — | Не читается |
| `editOffer` (`offers.py:94-129`) | **PATCH** | `offers/{offer_id}` | JSON: `{"amount": "<str(float)>"}` (≥0.5) | Не читается |
| `myReceivedOffers` (`offers.py:337-363`) | GET | `offers/received` | query: `offset`, `limit` | `{"top_offers": [{"offer": GiftOffer}]}` |
| `myPlacedOffers` (`offers.py:390-418`) | GET | `offers/placed` | query: `offset`, `limit` | `{"offers": [GiftOffer…]}` |
| `collectionOffer` (`offers.py:133-186`) | POST | `collection-offers/` | JSON: `{"amount": "<str>", "collection_id": "<UUID>", "expiration_days": 0\|7, "max_nfts": int}` | Не читается |
| `editCollectionOffer` (`offers.py:188-226`) | POST | `collection-offers/update` | JSON: `{"amount": "<str(float)>", "id": "<offer id>", "max_nfts": int}` | Не читается |
| `cancelCollectionOffer` (`offers.py:228-261`) | POST | `collection-offers/cancel` | JSON: `{"id": "<offer id>"}` | Не читается |
| `allCollectionOffers` (`offers.py:263-298`) | GET | `collection-offers/{collection_uuid}/all` | — | Массив `[CollectionOffer…]` на верхнем уровне |
| `topOffer` (`offers.py:300-333`) | GET | `collection-offers/{collection_uuid}/top` | — | `CollectionOffer` (объект или массив — класс берёт `[0]`, `Objects.py:101-104`) |
| `myCollectionOffers` (`offers.py:365-388`) | GET | `collection-offers/` | — | Массив `[CollectionOffer…]` |
| `getGiveaways` (`gifts.py:320-347`) | GET | `giveaways/` | query: `offset`, `limit`, `status=active` | `{"giveaways": [...]}` |
| `giveawayInfo` (`gifts.py:349-380`) | GET | `giveaways/{id}/requirements` | — | `GiveawayRequirements` |
| `joinGiveaway` (`gifts.py:382-414`) | POST | `giveaways/{id}/join` | — | 204 |

Сортировки `sort_by` — из кода (`utils/other.py:1-9`): `listed_at+desc` (latest), `price+asc`, `price+desc`, `external_collection_number+asc|desc` (номер подарка), `model_rarity+asc|desc`.

Справочник `utils/collections_ids.py`: локальная таблица «имя коллекции → UUID Portals», около 100 коллекций; её дописывают сторонние контрибьюторы. Это данные, а не логику; у себя их лучше брать из ответа `GET collections` (поле `id`), а не держать руками.

### Модель данных подарка (`aportalsmp/classes/Objects.py`) — основа нашей схемы
Все классы хранят сырой dict (`self.__dict__ = data`). Ниже перечислены поля, которые читает библиотека; в API могут быть и другие.

**PortalsGift** (`Objects.py:3-98`) — элемент `search.results`, `nfts/owned.nfts`, `actions[].nft`, `offer.nft`:
| Поле API | Тип (по коду) | Свойство |
|---|---|---|
| `id` | str (UUID листинга/NFT у Portals; используется в buy/sale) | `id` |
| `external_collection_number` | int/str (номер подарка в Telegram) | `tg_id` |
| `collection_id` | str (UUID коллекции) | `collection_id` |
| `name` | str | `name` |
| `photo_url` | str | `photo_url` |
| `price` | строка TON → float | `price` |
| `floor_price` | строка TON → float | `floor_price` |
| `attributes[]` | список `{type: "model"\|"symbol"\|"backdrop", value: str, rarity_per_mille: число}` | `model`, `model_rarity`, `symbol`, `symbol_rarity`, `backdrop`, `backdrop_rarity` |
| `listed_at` | str (дата) | `listed_at` |
| `status` | str (`listed`/`unlisted`/…) | `status` |
| `animation_url` | str | `animation_url` |
| `emoji_id` | str | `emoji_id` |
| `unlocks_at` | str (дата; блокировка передачи / premarket) | `unlocks_at` |

**CollectionOffer** (`Objects.py:100-163`): `id, collection_id, sender_id, amount (str→float), max_nfts, current_nfts, status, created_at, updated_at, expires_at, collection{name, short_name, photo_url, floor_price}`.
**GiftOffer** (`Objects.py:165-200`): `id, amount (str→float), status, created_at, updated_at, expires_at, nft (PortalsGift)`.
**Balances** (`Objects.py:264-277`): `balance, frozen_funds`. **Stats** (`245-262`): `total_bought, total_sold, total_volume`. **Points** (`202-243`): см. таблицу.
**Filters** (`Objects.py:279-305`): словари `models`, `backdrops`, `symbols` вида «имя → флор». **GiftsFloors** (`307-315`): `short_name → флор`. **CollectionItem** (`327-361`): `id, name, short_name, photo_url, day_volume, volume, floor_price, supply`.
**Activity** (`363-388`) / **MyActivity** (`390-447`) / **SaleResult** (`449-462`): см. таблицу эндпоинтов.
**Giveaway / GiveawayPrize / GiveawayChannel / GiveawayRequirements** (`464-698`): в GiveawayPrize поля подарка идут с префиксом `nft_` (`nft_id, nft_name, nft_photo, nft_animation_url, nft_emoji_id, nft_status, nft_collection_id, nft_external_collection_number, nft_attributes, nft_floor_price`, `position`). Для флиппера не нужны.

### Прочие пункты шаблона
- Источник данных: только REST, polling на стороне пользователя. WebSocket нет. Частоты и лимитов в коде нет.
- Оценка/флор: собственного алгоритма нет; флор берётся готовым из `collections/floors` и `collections/filters`.
- Комиссии: в коде не найдено.
- Предохранители и лимиты: только валидация аргументов (цена > 0, непустой id). Нет ни подтверждений, ни лимитов трат, ни dry-run.
- Уведомления / UI: нет (библиотека).
- Хранение состояния: нет, кроме файла сессии pyrogram.

## Отличия от синхронного portalsmp (сравнение с клоном bleach-hub__portalsmp, `portalsmp/portalsapi.py`, последний коммит 2025-08-07)
- **Домен:** async — `portal-market.com` (с 2025-11-06), sync — `portals-market.com`.
- **search:** async фильтрует коллекции через `collection_ids=<UUID,…>` и добавляет `exclude_bundled` и `premarket_status`; sync — через `filter_by_collections=<имена>` (`portalsapi.py:124-126`). `marketActivity` в обеих версиях ещё использует `filter_by_collections` с именами.
- **Points:** `points/me` (async) против `points/my-points` (sync).
- **Есть только в async:** `myStats` (`users/profile/stats`), `editCollectionOffer` (`collection-offers/update`), `transferGifts` (`nfts/transfer-gifts`), `withdrawGifts` (`nfts/withdraw`), `getGiveaways`/`giveawayInfo`/`joinGiveaway` (`giveaways/…`), прокси в `search`, сырой JSON-ответ в `buy`.
- **Совпадает:** `update_auth` (тот же бот `portals`, short_name `market`, platform `desktop`, формат `tma …`), тела `buy`/`sale`/`bulkList`/`changePrice`, офферы, `users/wallets/`, сортировки, `impersonate="chrome110"`. Sync использует синхронный `curl_cffi.requests` (`portalsapi.py:7`), async — `AsyncSession`.
- Живость: sync заархивирован (по прошлой версии отчёта portalsmp), последний коммит 2025-08-07. Async обновлялся до 2025-11-30 и с тех пор молчит около 11 месяцев. Эндпоинты могли поменяться: актуальность нужно проверить живым read-only запросом на Этапе 1.

## Что берём
| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Базовый URL `https://portal-market.com/api/`, набор заголовков (Origin/Referer/Accept), TLS-имитация curl_cffi | `markets/portals.py`, `docs/MARKETS.md#portals` | Формат API; клиент пишем сами |
| Получение initData: `@portals` → `RequestAppWebView(short_name="market", platform="desktop")` → `tma <initData>` | `auth/` (на Telethon: `messages.RequestAppWebViewRequest`) | Переписать |
| Эндпоинты и тела `search`, `collections/floors`, `collections/filters`, `collections`, `market/actions/`, `users/actions/`, `nfts` (buy), `nfts/bulk-list`, `nfts/{id}/list`, `users/wallets/`, офферы | `markets/portals.py`, `docs/MARKETS.md` | Формат API |
| Схема PortalsGift (`id, external_collection_number, collection_id, name, price, floor_price, attributes[type,value,rarity_per_mille], listed_at, status, unlocks_at…`) | `models/` (pydantic-схема ответа) | Переписать |
| Разбор ответа buy (`total_purchased`, `purchase_results[].status/reason`) как источник истины об успехе покупки | `execution.spend()` | Идея |
| `premarket_status` / `exclude_bundled` в поиске, `unlocks_at` | `rules/` (фильтр подарков, которые нельзя сразу перепродать) | Идея |

## Что НЕ берём и почему
- Пакет как зависимость не ставим (D-007). Фрагменты кода переносить можно с указанием источника (D-013), но переписывая под наши правила: Decimal/nanoTON вместо `str(float)`, ретраи и backoff, без голого `except`.
- Архитектуру HTTP-слоя: новая сессия на каждый запрос, нет ретраев, backoff и обработки 429, голый `except`, прокси только в одной функции. У нас: общий клиент, throttle, backoff на 429/5xx, jitter.
- Формирование цены через `str(float)`: у нас `Decimal` с фиксированной точностью.
- Локальную таблицу `collections_ids` — брать UUID из `GET collections`.
- Розыгрыши, transfer, withdrawGifts — к флиппингу не относятся (withdraw «NOT TESTED» самим автором).

## Открытые вопросы
- Нужна ли авторизация для `nfts/search`, `collections/floors`, `collections` (библиотека требует её всегда; проверять на Этапе 1 read-only запросом).
- Срок жизни `tma`-initData у Portals и код ответа при протухании (401/403?) — в коде не найдено.
- Лимиты запросов Portals и формат ответа 429 — в коде не найдено.
- Точность цен (сколько знаков после запятой принимает API) и минимальная цена листинга — в коде не найдено (есть только проверка ≥0.5 для офферов в библиотеке).
- Комиссия маркета при продаже — в коде не найдено.
- Полный формат `SaleResult.successful_nfts/failed_nfts` и ответа `changePrice` — в коде не найдено.
- Поведение `buy` при изменившейся цене (сравнивает ли сервер переданную `price` с текущей) — из кода не следует; в примере ответа есть только `reason: INSUFFICIENT_BALANCE`.

## Для MARKETS.md
Portals — по коду aportalsmp @ `d1daafd` (2025-11-30); живыми запросами не проверено.
- Base: `https://portal-market.com/api/` (из кода `utils/other.py:11`; старый домен `portals-market.com` заменён 2025-11-06).
- Auth: заголовок `Authorization: tma <initData>`; initData — из URL `RequestAppWebView(peer=@portals, app=InputBotAppShortName(short_name="market"), platform="desktop")`, кусок между `tgWebAppData=` и `&tgWebAppVersion`, после `unquote` (из кода `auth.py:30-44`).
- Заголовки: `Origin`/`Referer: https://portal-market.com(/)`, `Accept: application/json, text/plain, */*`, UA Chrome/Edge 137; curl_cffi `impersonate="chrome110"`, timeout 15 с (из кода `utils/other.py:13-21`, `handlers.py:11-31`).
- Цены: TON, десятичные **строки** в запросах и ответах (`"price": "1.85"`), не nano (из кода `gifts.py:567`, `offers.py:138`, `Objects.py:31`).
- `GET nfts/search?offset&limit&sort_by=price+asc&collection_ids=<uuid,…>&filter_by_models=&filter_by_backdrops=&filter_by_symbols=&min_price=&max_price=&status=listed&exclude_bundled=true&premarket_status=all` → `{results:[gift]}` (из кода `gifts.py:160-228`).
- `GET collections/floors` → `{floorPrices:{short_name: price}}`; `GET collections/filters?short_names=<sn>` → `{floor_prices:{sn:{models,backdrops,symbols}}}`; `GET collections?limit=100` → `{collections:[{id,name,short_name,floor_price,day_volume,volume,supply,photo_url}]}` (из кода `gifts.py:17-106`).
- `GET market/actions/?offset&limit&sort_by&action_types=buy,listing,price_update,offer&filter_by_collections=<имена>…` → `{actions:[{nft,type,amount,offer_id,created_at}]}`; `GET users/actions/?offset&limit` → `{actions:[…]}` (из кода `gifts.py:230-318,451-478`).
- Buy: `POST nfts` `{"nft_details":[{"id":"<uuid>","price":"<str>"}]}` → `{total_requested,total_purchased,total_failed,total_spent,purchase_results:[{id,status,reason,price,error_message}]}`; успех определять по `total_purchased`/`status`, не по HTTP-коду (из кода `gifts.py:525-580`).
- Листинг: `POST nfts/bulk-list` `{"nft_prices":[{"nft_id":"<uuid>","price":"<str>"}]}` → `{successful_nfts,failed_nfts}`; смена цены: `POST nfts/{id}/list` `{"price":"<str>"}` (из кода `gifts.py:582-697`).
- Баланс: `GET users/wallets/` → `{balance,frozen_funds}`; вывод TON: `POST users/wallets/withdraw` `{"amount":"<str>","external_address":"<addr>"}` → `{id}` (из кода `account.py:64-129`).
- Свои NFT: `GET nfts/owned?offset&limit&status=listed|unlisted` → `{nfts:[gift]}` (из кода `gifts.py:418-449`).
- Офферы: `POST offers` `{"offer":{"nft_id","offer_price":"<str>","expiration_days":7}}`; `PATCH offers/{id}` `{"amount"}`; `POST offers/{id}/cancel`; `GET offers/received|placed?offset&limit`; коллекционные: `POST collection-offers/` `{amount,collection_id,expiration_days,max_nfts}`, `POST collection-offers/update|cancel`, `GET collection-offers/{coll_uuid}/all|top` (из кода `offers.py`).
- Схема gift: `id, external_collection_number, collection_id, name, photo_url, price, floor_price, attributes[{type: model|symbol|backdrop, value, rarity_per_mille}], listed_at, status, animation_url, emoji_id, unlocks_at` (из кода `Objects.py:3-98`).
- Ошибки: тело не-2xx содержит `message` (из кода `handlers.py:43-47`); обработки 429 и лимитов в коде нет.
