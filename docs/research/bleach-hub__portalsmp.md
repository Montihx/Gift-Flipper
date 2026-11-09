# bleach-hub/portalsmp

Источник: исходники, клон от 2026-11-09, коммит `77fb2177d70019a2e52bf32ff4b613c2228703f2` (2025-08-07). Прочитаны как текст: `portalsmp/portalsapi.py` (1134 строки), `portalsmp/__init__.py`, `portalsmp/collections_ids.py`, `README.md`, `LICENSE`, история `git log -p`. Ничего не запускалось. Ниже ссылки вида `portalsapi.py:N` относятся к `portalsmp/portalsapi.py`.

- Ссылка: https://github.com/bleach-hub/portalsmp (PyPI: `portalsmp`)
- Язык / стек: Python. HTTP: `curl_cffi.requests` с `impersonate="chrome110"` (portalsapi.py:7, 155 и далее во всех запросах). Telegram: `pyrogram` (по README с версии 1.2 зависимость заменена на kurigram, который ставится под тем же именем модуля `pyrogram`; в коде импорт `from pyrogram import Client`, portalsapi.py:3). Файлов сборки (setup.py/pyproject) в репозитории нет.
- Лицензия: MIT (`LICENSE`, «Copyright (c) 2025 bleach»).
- Последний коммит / активность: 2025-08-07 (коммит «x», правка README). Последнее изменение кода: 2025-06-22 (версия 1.2, коммит b37ef68). Первый коммит 2025-06-14. Статус «архивирован» в клоне не проверяется (по прошлому проходу через страницу GitHub — архивирован 14.09.2025, не перепроверено).
- Звёзды / форки / коммиты: звёзды и форки не установлены; коммитов 21 (полная история, клон не упёрся в 50).
- Доверие: высокое для чтения как справочника. Код простой и читаемый, нет обфускации, `exec`/`eval`, base64, скачивания бинарников, отправки сессии или данных на сторонние адреса: все запросы идут только на `API_URL`. Секретов в коде нет. Минусы: заброшен с июня 2025, базовый домен с тех пор сменился (см. сверку с boostNT), ретраев и таймаутов нет.

## Что делает (2–3 предложения)

Синхронная Python-обёртка над неофициальным REST API маркета Portals (Telegram Mini App `@portals`, short_name `market`): поиск лотов, флоры коллекций и атрибутов, лента активности маркета, свой инвентарь, баланс и очки, покупка, листинг (одиночный и пакетный), смена цены, офферы на конкретный NFT и на коллекцию, вывод TON. Плюс асинхронная функция `update_auth()`, которая через пользовательскую MTProto-сессию получает `initData` и собирает заголовок `Authorization: tma …`.

## Как устроено

### Базовый URL и общие заголовки

Точная строка из кода (portalsapi.py:65):

```python
API_URL = "https://portals-market.com/api/"
```

То есть домен **portals-market.com** (с «s»), путь `/api/`, слэш в конце. Все пути ниже приклеиваются к нему конкатенацией строк.

Заголовки — один глобальный словарь `HEADERS` (portalsapi.py:67-75):

| Заголовок | Значение (из кода) |
|---|---|
| `Authorization` | пусто в шаблоне; перед каждым запросом перезаписывается `HEADERS["Authorization"] = authData` (напр. portalsapi.py:153) |
| `Accept` | `application/json, text/plain, */*` |
| `Accept-Encoding` | `gzip, deflate, br, zstd` |
| `Accept-Language` | `en-US,en;q=0.9,ru;q=0.8` |
| `Origin` | `https://portals-market.com` |
| `Referer` | `https://portals-market.com/` |
| `User-Agent` | десктопный Edge 137 на Windows (`Mozilla/5.0 (Windows NT 10.0; Win64; x64) … Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0`) |

`Content-Type` явно не задаётся: для POST/PATCH тело передаётся через `json=PAYLOAD`, библиотека сама ставит JSON (из кода, напр. portalsapi.py:458). TLS-отпечаток — `impersonate="chrome110"`, т.е. отпечаток Chrome 110 при User-Agent Chrome/Edge 137 (несоответствие, из кода). Глобальный `HEADERS` мутируется при каждом вызове — при многопоточном использовании с разными аккаунтами токены перепутаются (из кода).

### Авторизация: `update_auth()` (portalsapi.py:28-53)

```python
async with Client("account", api_id=api_id, api_hash=api_hash) as client:
    peer = await client.resolve_peer("portals")
    user_full = await client.invoke(GetUsers(id=[peer]))
    bot_raw = user_full[0]
    bot = InputUser(user_id=bot_raw.id, access_hash=bot_raw.access_hash)
    bot_app = InputBotAppShortName(bot_id=bot, short_name="market")
    web_view = await client.invoke(
        RequestAppWebView(peer=peer, app=bot_app, platform="desktop"))
    initData = unquote(web_view.url.split('tgWebAppData=', 1)[1].split('&tgWebAppVersion', 1)[0])
    return f"tma {initData}"
```

- Сессия Pyrogram/kurigram с именем `"account"` (файл `account.session` в текущем каталоге), нужны `api_id`, `api_hash` и интерактивный вход при первом запуске (portalsapi.py:39).
- Бот (peer): `"portals"` — `resolve_peer("portals")` (portalsapi.py:40); `access_hash` бота берётся сырым вызовом `users.GetUsers` (portalsapi.py:41-43).
- Метод: raw `messages.RequestAppWebView` (не `RequestWebView`) с `InputBotAppShortName(bot_id=<InputUser>, short_name="market")`, `platform="desktop"` (portalsapi.py:44-51). Параметры `start_param`, `write_allowed`, `url` не передаются.
- Выделение initData: из `web_view.url` берётся подстрока между `tgWebAppData=` и `&tgWebAppVersion` (фрагмент URL после `#`), затем **один раз** `urllib.parse.unquote` (portalsapi.py:52). То есть в заголовок идёт URL-декодированная строка вида `query_id=…&user=…&auth_date=…&signature=…&hash=…` — внутренние значения (например JSON `user=`) после одного `unquote` остаются в том виде, в каком были внутри tgWebAppData (одинарно закодированными). Точный набор полей в коде не перечисляется.
- Итоговая строка: `"tma " + initData` (portalsapi.py:53); она и есть значение заголовка `Authorization` для всех функций (параметр `authData`).
- Кэширования, проверки срока, автоперевыпуска нет: функция просто возвращает строку (из кода). Срок жизни: README говорит про токен из Telegram Web «вероятно 1–7 дней» (оценка автора, README:66); в коде срок не обрабатывается.
- Каждая HTTP-функция проверяет только, что `authData` не пустой, и бросает `Exception` иначе (напр. portalsapi.py:117-118).

### Таблица эндпоинтов (всё — из кода `portalsapi.py`)

Обозначение `{API}` = `https://portals-market.com/api/`. Все запросы: заголовки `HEADERS` (см. выше) + `Authorization: tma …`, `impersonate="chrome110"`.

| Функция (строки) | Метод | Путь | Query / тело | Что код читает из ответа |
|---|---|---|---|---|
| `search` (77-159) | GET | `{API}nfts/search?offset={int}&limit={int}&sort_by=…` | `offset`, `limit` (по умолч. 20; докстринг: «probably max is 20»); `sort_by` из `SORTS` (см. ниже); `min_price`, `max_price` — целые, добавляются **только если** `max_price < 100000` (114-115); `filter_by_collections`, `filter_by_models`, `filter_by_backdrops`, `filter_by_symbols` — имена (см. «Кодирование фильтров»); всегда `&status=listed` (151) | `["results"]`; если список пуст — возвращает весь JSON (159) |
| `giftsFloors` (161-187) | GET | `{API}collections/floors` | нет | `["floorPrices"]` (camelCase), ключи — short names коллекций (по докстрингу) |
| `filterFloors` (951-980) | GET | `{API}collections/filters?short_names={short}` | `short` = `toShortName(gift_name)`: убрать пробелы, `'`, `’`, `-`, lower (25-26, 971) | `["floor_prices"][short]`; внутри по докстрингу ключи `models`, `backdrops`, `symbols` (958) |
| `collections` (306-332) | GET | `{API}collections?limit={int}` | `limit` по умолч. 100 | `["collections"]` |
| `marketActivity` (334-420) | GET | `{API}market/actions/?offset=&limit=&sort_by=…` | те же `offset/limit/sort_by/min_price/max_price/filter_by_*`, что у search; `action_types=` — `buy`, `listing`, `price_update`, `offer`, список склеивается через `%2C` (379-382, 412-413); `status` не передаётся | `["actions"]` (если ключ есть) |
| `myActivity` (277-304) | GET | `{API}users/actions/?offset=&limit=` | `offset`, `limit` (20) | `["actions"]` |
| `myPortalsGifts` (189-221) | GET | `{API}nfts/owned?offset=&limit=&status=listed\|unlisted` | `listed=True` → `status=listed`, иначе `unlisted` (210-213) | `["nfts"]` |
| `myBalances` (250-275) | GET | `{API}users/wallets/` | нет | весь JSON, поля не разбираются (в коде не найдено, какие ключи) |
| `myPoints` (223-248) | GET | `{API}points/my-points` | нет | весь JSON |
| `buy` (507-550) | POST | `{API}nfts` | `{"nft_details": [{"id": <nft_id:str>, "price": str(price)}]}` (537, 542-544) | 200 → JSON, 204 → `None` |
| `sale` (464-505) | POST | `{API}nfts/bulk-list` | `{"nft_prices": [{"nft_id": <str>, "price": str(price)}]}` (493, 497-499) | 200 → JSON, 204 → `None` |
| `bulkList` (428-462) | POST | `{API}nfts/bulk-list` | `{"nft_prices": nfts}`, элементы `{"nft_id", "price"}` — готовит `convertForListing()` (422-423) | 200 → JSON, 204 → `None`. README: «Not tested yet» |
| `changePrice` (635-674) | POST | `{API}nfts/{nft_id}/list` | `{"price": str(price)}` (666-668) | 200/204 |
| `makeOffer` (552-601) | POST | `{API}offers` | `{"offer": {"nft_id": <str>, "offer_price": str(offer_price), "expiration_days": 7}}`; ключ `expiration_days` добавляется только при 7, при 0 (бессрочно) отсутствует (587-595) | 200/204 |
| `cancelOffer` (603-633) | POST | `{API}offers/{offer_id}/cancel` | тела нет (629) | 200/204 |
| `editOffer` (1011-1043) | PATCH | `{API}offers/{offer_id}` | `{"amount": str(float(new_price))}`; локальная проверка `new_price >= 0.5` (1030, 1035-1037) | 204 → `None`, иначе JSON |
| `myPlacedOffers` (982-1009) | GET | `{API}offers/placed?offset=&limit=` | | `["offers"]` |
| `myReceivedOffers` (1045-1072) | GET | `{API}offers/received?offset=&limit=` | | `["top_offers"]` |
| `collectionOffer` (834-895) | POST | `{API}collection-offers/` | `{"amount": str(amount), "collection_id": <uuid из collections_ids>, "expiration_days": 0\|7, "max_nfts": int}` (883-888) | принимает 200/201/204; 200/201 → JSON («id, collection_id, status etc.» по докстрингу) |
| `cancelCollectionOffer` (897-917) | POST | `{API}collection-offers/cancel` | `{"id": <offer_id>}` (908-910) | 200/204 |
| `allCollectionOffers` (919-949) | GET | `{API}collection-offers/{collection_id}/all` | | весь JSON |
| `topOffer` (1101-1134) | GET | `{API}collection-offers/{collection_id}/top` | | весь JSON |
| `myCollectionOffers` (1074-1099) | GET | `{API}collection-offers/` | | весь JSON |
| `withdrawPortals` (794-832) | POST | `{API}users/wallets/withdraw` | `{"amount": str(amount), "external_address": <str>}` (823-826) | 200 → JSON («ID of the withdrawal» по докстрингу) |

Сортировки `SORTS` (portalsapi.py:55-63): `latest` → `sort_by=listed_at+desc`; `price_asc/desc` → `price+asc/desc`; `gift_id_asc/desc` → `external_collection_number+asc/desc`; `model_rarity_asc/desc` → `model_rarity+asc/desc`. Те же значения используются и для `market/actions/`.

Кодирование фильтров по именам (portalsapi.py:11-23, 122-149): каждое слово имени делается с заглавной буквы функцией `cap()` (`"toy bear"` → `"Toy Bear"`, апостроф внутри слова сохраняется), затем `quote_plus` (пробел → `+`); список склеивается уже закодированной запятой `%2C`. Фильтр по коллекции — **по имени** (`filter_by_collections=Toy+Bear`), не по UUID.

История тела `buy` (git): в 1.0 (7b6cff8, 2025-06-14) было `{"id", "owner_id", "price"}`, в 1.0.1 (d0b6f07) `owner_id` убран. В коде остался комментарий-пример из перехваченного запроса: `{"nft_details":[{"id":"aaaa8eb4-…","owner_id":6540727795,"price":"1.85"}]}` (portalsapi.py:538-540). README (строка 280) до сих пор показывает старую сигнатуру `buy(nft_id, owner_id, price, …)` — документация отстала от кода. В 1.0.1 же исправлен `makeOffer`: ключ цены `price` → `offer_price`, `expiration_days` перенесён внутрь `offer`.

### Цены и единицы

- Во всех телах запросов цена — **строка**, получаемая `str(price)` из Python-числа: `buy`, `sale`, `bulkList` (через `convertForListing`), `changePrice`, `makeOffer`, `collectionOffer`, `withdrawPortals`; в `editOffer` — `str(float(new_price))` (из кода, строки выше).
- Округления, `Decimal`, фиксированной точности нет. `str()` от float может дать `0.30000000000000004` или `1e-05` (свойство Python, в коде никак не обработано).
- Проверки: в `buy`/`sale` цена должна быть ненулевым `int` или `float` (`type(price) not in [int, float]` → ошибка, 490, 532); в `changePrice`, `makeOffer`, `withdrawPortals` проверяется только `!= 0`; `editOffer` — число `>= 0.5` (1030); `collectionOffer` — `> 0` (862).
- Единица: в коде прямо не названа. Признаки, что это **TON в десятичной записи, не nano**: пример в коде `"price":"1.85"` (539), минимум оффера `0.5` (1030), в README ответ поиска `"price": "44"`, `"floor_price": "31.43"` (README:105, 128), вывод `withdrawPortals` описан как «to your TON wallet» (README:381). Вывод «TON» — наш, явной константы нет.
- В ответах цены тоже строки; класс `PortalsGift` приводит `price` и `floor_price` к `float` (726, 788).
- Фильтры `min_price`/`max_price` в query приводятся к `int` (108-112) — дробные границы невозможны. Баг: при `max_price=100000` (по умолчанию) `min_price` не отправляется вовсе (114-115).
- Передаётся ли в `buy` текущая цена лота и проверяет ли сервер совпадение — в коде не найдено (код просто шлёт то, что дали).

### Модель данных подарка (`PortalsGift`, portalsapi.py:676-792; пример ответа README:96-130)

Поля объекта из `nfts/search`: `id` (UUID Portals), `tg_id`, `collection_id` (UUID), `external_collection_number` (номер подарка; свойство `PortalsGift.tg_id` возвращает именно его, 708-710 — путаница с полем `tg_id`), `owner_id` (в README-примере; из класса убран в 1.0.1), `name`, `photo_url` (nft.fragment.com), `price` (строка), `attributes[]` с `{type: model|symbol|backdrop, value, rarity_per_mille}`, `listed_at` (ISO), `status`, `animation_url`, `emoji_id`, `has_animation`, `floor_price` (строка; флор коллекции, не модели), `unlocks_at`.

### Оценка / флор

Своей логики оценки нет. Источники флора: `GET collections/floors` (все коллекции, ключи short names), `GET collections/filters?short_names=…` (флоры моделей/фонов/символов одной коллекции), `GET collections?limit=` (флоры, supply, дневной объём — по докстрингу 308), поле `floor_price` в каждом лоте поиска.

### Комиссии

В коде и README не найдены. Цифры Portals (0% покупка / 5% продажа / 0.1 TON вывод) остаются непроверенными.

### Обработка ошибок, ретраи, лимиты

- Любой код, кроме 200 (GET) или 200/204 (POST/PATCH; у `collectionOffer` ещё 201), → `raise Exception("portalsmp: <func>(): Error: status_code: …, response_text: …")` (напр. 156-157, 459-460). Отдельной обработки 401/403/429/5xx нет.
- Ретраев, backoff, таймаутов (`timeout=` не передаётся ни в одном запросе), throttle — нет (из кода).
- Разбор ответа хрупкий: `response.json()["results"]` бросит `KeyError`, если ключа нет; при пустом списке функции возвращают весь JSON вместо `[]` (159, 304, 332) — тип возврата непостоянный.
- Лимиты API: в коде не найдены; `limit` поиска по докстрингу «probably max is 20» (86).

### `collections_ids.py`

Словарь `collections_ids = { "<Название коллекции>": "<UUID Portals>" }` — 75 записей, без дублей ключей и значений (подсчёт по тексту файла). Ключи в виде «Title Case», как отображаются в Portals: `"Plush Pepe"`, `"Durov's Cap"`, `"Jack-in-the-Box"`, `"B-Day Candle"` … `"Winter Wreath"`. Значения — UUID, например `"Toy Bear": "060d4cef-3a21-47e6-98fc-cd338ae0b5e0"` (совпадает с `collection_id` в README-примере). Файл создан 2025-06-17 (c9398c2) и больше не обновлялся — коллекций, вышедших позже, нет. Используется только для офферов на коллекцию (`collectionOffer`, `allCollectionOffers`, `topOffer`): имя прогоняется через `cap()` и ищется в словаре (874-879, 1120). Поиск `search` UUID не использует.

### Прочее

- `__init__.py` делает `from portalsmp.portalsapi import *`, а в `__all__` перечислены только функции версии 1.0 (без офферов на коллекцию, `filterFloors` и т.д.) — косметика.
- Async-версия `aportalsmp` в этом репозитории отсутствует, только ссылка в README (строка 12); разобрана в отдельном отчёте `bleach-hub__aportalsmp.md`.
- Уведомления / UI: нет (библиотека). Хранение состояния: только файл сессии `account.session` от Pyrogram.

## Что берём

| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Таблица эндпоинтов Portals (поиск, флоры, активность, инвентарь, баланс, buy, bulk-list, list, offers, collection-offers, withdraw) | `docs/MARKETS.md#portals`, `markets/portals.py` | Формат API; переписать свой клиент. Базовый домен сделать настройкой (см. сверку: сейчас по boostNT `portal-market.com`) |
| Схема получения initData: `messages.requestAppWebView`, бот `portals`, short_name `market`, вырезать `tgWebAppData`, `unquote`, префикс `tma ` | `markets/portals.py` (авторизация через Telethon) | Переписать на Telethon (`functions.messages.RequestAppWebViewRequest`), токен держать в памяти/секретах, перевыпуск при 401/403 |
| Тело `buy`: `{"nft_details":[{"id","price"}]}`, цена — десятичная строка в TON | `markets/portals.py`, `execution.spend()` | Формировать цену из `Decimal` с явным форматированием (без float), брать цену из свежего лота |
| Тела листинга/смены цены/офферов | `markets/portals.py` (не MVP для офферов) | Формат API |
| Сортировки и фильтры поиска, кодирование имён (Title Case + `quote_plus`, запятая `%2C`) | `markets/portals.py` | Формат API; сверить с живым ответом и с `collection_ids` из boostNT |
| `collections_ids.py` как стартовый маппинг имя → UUID | `pricing/aliases.py` | Не копировать; строить маппинг динамически из `GET collections` и кэшировать |
| Заголовки Origin/Referer/UA + TLS-имперсонация (`curl_cffi`) | `markets/portals.py` | Идея; UA и `impersonate` согласовать между собой |

## Что НЕ берём и почему

- Глобальный изменяемый `HEADERS` — небезопасно при параллельных запросах.
- `str(float)` для цен — риск неверной строки цены при покупке; у нас только `Decimal`.
- Отсутствие таймаутов, ретраев, backoff на 429/5xx — противоречит AGENTS.md §4 п.5.
- `collections_ids.py` статичный и устаревший (75 коллекций на июнь 2025).
- `withdrawPortals` — необратимое действие, в MVP не реализуем.
- Сам пакет не ставим и не запускаем.

## Открытые вопросы

- Какой домен актуален: в коде `portals-market.com`, в README boostNT (с 2025-11-06) — `portal-market.com`. Проверить на живом запросе.
- Работает ли ещё `filter_by_collections` (по имени) или нужен `collection_ids` (UUID), как пишет boostNT с ноября 2025.
- Реальный максимум `limit` для `nfts/search` (portalsmp: «вероятно 20», boostNT: 100).
- Формат ответа `users/wallets/` (поля баланса) и `points/my-points` — код их не разбирает.
- Что возвращает `POST nfts` (покупка) при успехе и при «лот уже продан/цена изменилась»: в коде не описано.
- Проверяет ли сервер, что `price` в `buy` совпадает с ценой лота.
- Срок жизни `tma`-токена (README: 1–7 дней для Telegram Web, оценка автора).
- Комиссии Portals.

## Для MARKETS.md

- Базовый URL в portalsmp: `https://portals-market.com/api/` (из кода, portalsapi.py:65). Расхождение: boostNT README с 2025-11-06 — `https://portal-market.com/api` (из README boostNT). Исторически: `market.portals.tg` (май 2025, история README boostNT).
- Авторизация: заголовок `Authorization: tma <initData>`; initData = `unquote(` подстрока `tgWebAppData=…` до `&tgWebAppVersion` из `web_view.url` `)`, где `web_view = messages.requestAppWebView(peer=@portals, app=InputBotAppShortName(bot=@portals, short_name="market"), platform="desktop")` (из кода, portalsapi.py:39-53). boostNT — то же, но `platform="android"` (из README).
- Заголовки: `Origin: https://portals-market.com`, `Referer: https://portals-market.com/`, UA Edge 137 Windows, `Accept: application/json, text/plain, */*`, TLS `curl_cffi impersonate="chrome110"` (из кода, 67-75, 155).
- `GET nfts/search?offset&limit&sort_by=<field>+<asc|desc>&min_price&max_price&filter_by_collections&filter_by_models&filter_by_backdrops&filter_by_symbols&status=listed` → `results[]` (из кода, 106-159). Значения фильтров — имена в Title Case, `quote_plus`, разделитель `%2C`.
- Сортировки: `listed_at+desc`, `price+asc|desc`, `external_collection_number+asc|desc`, `model_rarity+asc|desc` (из кода, 55-63).
- `GET collections/floors` → `floorPrices{short_name: …}`; `GET collections/filters?short_names=<short>` → `floor_prices[short]{models,backdrops,symbols}`; `GET collections?limit=` → `collections[]` (из кода).
- `GET market/actions/?offset&limit&sort_by&…&action_types=buy,listing,price_update,offer` → `actions[]` — лента продаж маркета (из кода, 364-420).
- `GET users/actions/?offset&limit` → `actions[]`; `GET nfts/owned?offset&limit&status=listed|unlisted` → `nfts[]`; `GET users/wallets/` (баланс, поля не разобраны); `GET points/my-points` (из кода).
- Покупка: `POST nfts` тело `{"nft_details":[{"id":"<nft uuid>","price":"<TON строкой>"}]}`; успех 200 или 204 (из кода, 526-550). До 1.0.1 в элементе был `owner_id` (из истории git).
- Листинг: `POST nfts/bulk-list` тело `{"nft_prices":[{"nft_id":"<uuid>","price":"<строка>"}]}`; смена цены: `POST nfts/{id}/list` тело `{"price":"<строка>"}` (из кода).
- Офферы: `POST offers` `{"offer":{"nft_id","offer_price":"<строка>","expiration_days":7}}` (ключ опускается для бессрочного); `POST offers/{id}/cancel`; `PATCH offers/{id}` `{"amount":"<строка>"}` (мин. 0.5 — локальная проверка); `GET offers/placed`, `GET offers/received` → `top_offers` (из кода).
- Офферы на коллекцию: `POST collection-offers/` `{"amount":"<строка>","collection_id":"<uuid>","expiration_days":0|7,"max_nfts":int}` (200/201/204); `POST collection-offers/cancel` `{"id"}`; `GET collection-offers/{collection_id}/top|/all`; `GET collection-offers/` (из кода).
- Вывод: `POST users/wallets/withdraw` `{"amount":"<строка>","external_address":"<адрес>"}` (из кода, 812-828; README: `UQ`-адреса «на свой риск»).
- Единицы: все цены — десятичные строки, по признакам TON (не nano): пример `"1.85"`, `"44"`, `"31.43"` (из кода 539 и README). Округления в клиенте нет.
- Ошибки/лимиты: только проверка кода ответа (200/204), без ретраев, таймаутов и обработки 429 (из кода). Лимиты API в коде не найдены.
