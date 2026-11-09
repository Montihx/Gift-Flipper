# TheBrainAir/amrkt

> Источник: исходники, клон от 2026-11-09, коммит `2a4dbf537434685fffef437e67a61dffeeb28a03` (2026-03-22). Прочитаны как текст все файлы: `amrkt/client.py` (702 строки), `amrkt/models.py` (428), `amrkt/exceptions.py`, `amrkt/__init__.py`, `README.md`, `LICENSE`; история `git log`, удалённые `.pyc` из коммита `08c4232` просмотрены через `strings`. Ничего не запускалось. Живых запросов не было: все факты «из кода» или «из README», на живом ответе не проверены.
>
> Обозначения: `client:NNN` = `amrkt/client.py:NNN`, `models:NNN` = `amrkt/models.py:NNN`, `exc:NNN` = `amrkt/exceptions.py:NNN`.

- Ссылка: https://github.com/TheBrainAir/amrkt (PyPI: `amrkt`, по README)
- Язык / стек: Python 3.9+ (README), async-обёртка. Зависимости по импортам: `pyrogram` (получение initData), `curl_cffi` (HTTP с имитацией TLS), `pydantic` v2 (`model_validate`, но `class Config` в стиле v1). `pyproject.toml`/`setup.py`/`requirements.txt` в репозитории **нет** (README предлагает `pip install -e .`, но собрать нечем), версии зависимостей не зафиксированы.
- Лицензия: MIT, Copyright (c) 2026 TheBrainAir (файл `LICENSE`).
- Последний коммит / активность: 2026-03-22 (`2a4dbf5`, «Add files via upload»); версия в коде `1.6.0` (`__init__.py:74`). Активность: январь–март 2026, далее коммитов нет (~7,5 месяцев на дату разбора).
- Звёзды / форки / коммиты: звёзды/форки — не установлено; коммитов — 15 (клон глубины 50 не упёрся, история полная).
- Доверие: **среднее/высокое**. Код маленький, читаемый, без обфускации, `exec`/`eval`/`base64`/`subprocess`/сокетов/вебхуков нет; сетевые адреса только `api.tgmrkt.io` (и Telegram через Pyrogram). Захардкоженных секретов нет. Удалённые `.pyc` (коммит `08c4232`, удалены в `c854801`) по строкам совпадают с исходником той версии (те же эндпоинты, никаких посторонних URL). Риски — качество, а не злонамеренность (см. «Что НЕ берём»).

## Что делает

Асинхронная (по интерфейсу) Python-библиотека-клиент для маркета MRKT (`api.tgmrkt.io`): авторизация через пользовательскую сессию Telegram (Pyrogram) → initData → токен MRKT; поиск листингов, карточка подарка, коллекции, покупка, листинг/снятие/смена цены, инвентарь, возврат подарка в Telegram, баланс, депозиты, лента рынка, офферы, активности пользователя. Своей логики (флор, правила, предохранители) нет — только тонкая обёртка над HTTP.

## Как устроено

### Базовое

- Базовый URL: `https://api.tgmrkt.io/api/v1` (`client:55`). Все пути ниже — относительно него.
- Транспорт: синхронные `curl_cffi.requests.get/post` **без Session**, вызываются внутри `async def` (`client:189`, `client:233`, `client:273-279`) — блокируют event loop, нет переиспользования соединений и cookie-jar. Таймаут явно не задан (используется дефолт `curl_cffi`).
- Polling/WebSocket: WebSocket в коде не найден. Частоты опроса нет (библиотека, а не бот).

### Таблица методов

Все запросы идут через `_request()` (`client:256-301`) с заголовками `_get_headers()` (см. ниже), кроме проверки токена и самого `auth`. Ответ всегда парсится как JSON, кроме мест с `expect_json=False`.

| Метод amrkt | HTTP | Полный URL | Тело / query (точные ключи, типы) | Поля ответа (как парсит amrkt) | Источник |
|---|---|---|---|---|---|
| `_get_new_token` (auth) | POST | `https://api.tgmrkt.io/api/v1/auth` | JSON `{"data": <initData: str>}` | `{"token": str}`; не 200 → `AuthenticationError("Auth failed: <code>")`; нет `token` → `AuthenticationError` | client:232-249 |
| `_is_token_valid` (проверка токена) | POST | `…/gifts/saling` | полный поисковый JSON с `"count": 1`, `"lowToHigh": false`, `"cursor": ""`, все фильтры пустые/`null` | смотрит только статус: `!= 401` → токен валиден; исключение → невалиден | client:182-203 |
| `get_user_info` | GET | `…/me` | — | `UserInfo` (см. модели) | client:305-313 |
| `get_balance` | GET | `…/balance` | — | `Balance`: `soft`, `hard`, `totalHard`, `hardLocked`, `stars`, `starsFotWithdraw`, `spices`, `friendsCount`, `luckyBuyCards`, `stackingPoints`, `spaceMonkeysPoints` | client:317-325, models:68-103 |
| `get_deposit_await` | GET | `…/transactions/await` | — | массив `DepositAwaitTransaction`: `id`, `currencyType`, `value`, `softValue`, `receivedAt`, `isClaimed`, `isRefunded` | client:327-335, models:106-122 |
| `claim_transaction` | POST | `…/transactions/{transaction_id}` | тело не передаётся (`json=None`) | массив `ClaimTransactionResult`: `value`, `type`, `source` | client:337-348, models:125-137 |
| `search_gifts` | POST | `…/gifts/saling` | JSON (все ключи всегда присутствуют): `collectionNames: [str]`, `modelNames: [str]`, `backdropNames: [str]`, `symbolNames: [str]`, `ordering: str` (по умолчанию `"Price"`), `lowToHigh: bool` (по умолчанию `true`), `maxPrice: int\|null`, `minPrice: int\|null`, `mintable: bool\|null`, `number: int\|null`, `count: int` (по умолчанию 20), `cursor: str` (первая страница `""`), `query: str\|null`, `promotedFirst: bool` (`false`) | `GiftList`: `gifts: [Gift]`, `total: int`, `cursor: str\|null` | client:352-409, models:261-268, 361-398 |
| `get_gift` | GET | `…/gifts/gift/{gift_id}` | — | `Gift` | client:411-422 |
| `get_collections` | GET | `…/gifts/collections` | — | массив `GiftCollection` (см. ниже) | client:424-432, models:271-298 |
| `buy_gifts` | POST | `…/gifts/buy` | JSON `{"Ids": [str]}` — **ключ с заглавной `I`**; цена **не передаётся** | если массив: `[{userGift: Gift, price: int}]` → `PurchaseResult`; иначе `[]` | client:434-451, models:301-312 |
| `get_inventory` | POST | `…/gifts` | тот же JSON, что у `search_gifts`, но по умолчанию `lowToHigh: false`, `count: 50` | `GiftList` | client:455-499 |
| `return_gifts` | POST | `…/gifts/return` | JSON `{"Ids": [str]}` (заглавная `I`) | ответ JSON парсится, но не используется; возвращает `True` | client:503-514 |
| `get_feed` | POST | `…/feed` | JSON `{}` (никаких фильтров, cursor, count) | `FeedResponse`: `items: [{type: str, id: str, gift: Gift, amount: int, date: datetime}]`; `type` по комментарию: `"listing"`, `"sale"`, `"change_price"` | client:518-528, models:315-337 |
| `sell_gifts` | POST | `…/gifts/sale` | JSON `{"ids": [str], "prices": [int]}` — **ключ строчный**, цены nanoTON, порядок совпадает с `ids`; длины проверяются локально (`ValueError`) | `SaleResult`: `ids: [str]`, `prices: [int]` | client:532-562, models:340-358 |
| `cancel_sale` (unsell) | POST | `…/gifts/sale/cancel` | JSON `{"ids": [str]}` | массив id снятых подарков (`[str]`), иначе `[]` | client:564-583 |
| `change_price` | POST | `…/gifts/sale/change-price` | JSON `{"ids": [str], "prices": [int]}` (nanoTON) | `SaleResult` | client:585-615 |
| `create_offer` | POST | `…/offers/create` | JSON `{"price": int (nanoTON), "giftSaleId": str}` | не парсится (`expect_json=False`), возвращает `True` | client:619-646 |
| `cancel_offer` | POST | `…/offers/cancel?offerId=<str>` | **query**-параметр `offerId`, тело `null` | не парсится, `True` | client:648-672 |
| `get_activities` | GET | `…/activities?offset=<int>&count=<int>&isActive=<"true"\|"false">` | query: `offset` (0), `count` (20), `isActive` (строка в нижнем регистре) | массив `ActivityItem`: `type: str`, `date: str`, `offer: ActivityOffer\|null` (`id`, `isMine`, `priceNanoTONs`, `ownerSalePrice`, `gift`, `createdAt`, `endAt`, `isNotificationSeen`) | client:676-702, models:401-428 |

В коде **не найдено**: отдельной истории продаж (`history`), списков моделей/фонов/символов (`models`/`backdrops`), офферов на коллекцию, списка входящих офферов (кроме `activities`), вывода средств (withdraw), пополнения, аукционов, WebSocket, эндпоинта цены/флора по модели (флор приходит только полями подарка и коллекции).

### Заголовки (client:108-129)

Одинаковые для всех запросов, включая `auth`:

```
Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate, br
Accept-Language: en-GB,en-US;q=0.9,en;q=0.8
Cache-Control: no-cache
Connection: keep-alive
Host: api.tgmrkt.io
Origin: https://cdn.tgmrkt.io
Pragma: no-cache
Priority: u=3, i
Referer: https://cdn.tgmrkt.io/
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-site
User-Agent: <случайный из списка или заданный>
Authorization: <token>          # только если токен есть; БЕЗ префикса Bearer
Cookie: access_token=<token>    # только если токен есть
```

Токен передаётся одновременно в `Authorization` (сырой, без `Bearer`) и в cookie `access_token` (client:126-128). `Content-Type` не задаётся явно — его ставит `curl_cffi` для `json=`.

### Авторизация: initData и токен

- initData получается через **Pyrogram** (не Telethon), пользовательская сессия (`api_id`/`api_hash`, файл `session_name` в `workdir`) (client:205-230):
  - `peer = resolve_peer("mrkt")` — бот `@mrkt`;
  - `InputBotAppShortName(bot_id=peer, short_name="app")`;
  - `messages.RequestAppWebView(peer=peer, app=bot_app, platform="android")` — без `start_param`, без `write_allowed`;
  - initData = `unquote( url.split("tgWebAppData=",1)[1].split("&tgWebAppVersion",1)[0] )` — один раз URL-декодированная строка из фрагмента URL веб-вью.
- Токен: `POST /auth {"data": initData}` → `token` (client:233-249). Формат токена в коде не описан.
- Хранение: только в памяти (`self._token`), на диск не пишется; новый экземпляр клиента = новый запуск Pyrogram + новый `RequestAppWebView` + новый `/auth`.
- Обновление: (1) перед **каждым** запросом `_ensure_authenticated()` вызывает `_is_token_valid()`, который делает лишний `POST /gifts/saling` c `count=1` и считает токен живым, если статус ≠ 401 (client:182-203, 251-254, 266); (2) если основной запрос вернул 401 — однократно получает новый токен и повторяет запрос (`retry_on_401=False` во второй раз) (client:281-287).
- Следствие: каждый вызов API = **2 HTTP-запроса** к MRKT (проверка + сам запрос). Для нас это анти-паттерн с точки зрения лимитов.
- Срок жизни токена: **в коде не найден**; библиотека полагается на 401.

### Единицы цен

- Везде nanoTON (`int`), 1 TON = 1 000 000 000:
  - `minPrice`/`maxPrice` в поиске — «in nanoTON» (докстринг client:379-380); тип `int` (models:369-370);
  - `prices` в `sell_gifts`/`change_price` — nanoTON (докстринги client:538, 591; примеры `10_000_000_000` = 10 TON);
  - `price` в `create_offer` — nanoTON (client:625);
  - в ответах: `salePrice`, `salePriceWithoutFee` (хелперы делят на 1e9, models:228-236), `floorPriceNanoTONsByCollection`, `floorPriceNanoTONsByBackdropModel` (models:181-182), `floorPriceNanoTons`/`previousDayFloorPriceNanoTons` у коллекции (models:277-280; обратите внимание на разный регистр `NanoTons` vs `NanoTONs`), `PurchaseResult.price`, `FeedItem.amount`, `ActivityOffer.priceNanoTONs`/`ownerSalePrice`, `Balance.soft/hard/totalHard/hardLocked`, депозиты `value`/`softValue` — все делятся на 1e9 в хелперах.
- `stars` — «Stars count» (README:117), не nanoTON.
- `salePrice` vs `salePriceWithoutFee`: в коде только «Sale price» / «Price without fee» (README:493-494); какая комиссия и кто её платит — не описано. Предположительно `salePrice` — цена для покупателя с комиссией, `salePriceWithoutFee` — сумма продавцу, но **это не подтверждено**.

### Балансы soft / hard / stars

- Поля `Balance` (models:68-80): `soft`, `hard`, `totalHard`, `hardLocked`, `stars`, `starsFotWithdraw` (опечатка «Fot» — так в alias, вероятно повторяет API), `spices`, `friendsCount`, `luckyBuyCards`, `stackingPoints`, `spaceMonkeysPoints`.
- Докстринги лишь «Soft balance in TON», «Hard balance in TON», «Total hard balance in TON», «Locked hard balance in TON» (models:85-103). README: `soft`/`hard` — «Raw values (in nanoTON)» (README:114-116).
- Депозиты имеют `currencyType` `"Hard"` или `"Soft"` (README:134, 456), клейм — `type` `"hard"`/`"soft"` (README:468) — т.е. оба — денежные балансы, на которые может зачисляться депозит.
- Quick Start печатает как «Balance» именно `balance.hard_ton` (README:57) — косвенно `hard` — основной TON-баланс. Смысл `soft` (бонусный/реферальный/кэшбэк?) **в коде не описан**.
- Какой баланс тратится при покупке: **в коде не найдено** — `buy_gifts` не передаёт ни цену, ни тип баланса (client:447); `PurchaseResult` содержит только `price`.

### Пагинация и `count`

- Поиск/инвентарь: курсорная. Запрос `cursor: ""` на первой странице, далее `cursor` из ответа (`GiftList.cursor`, models:265). Пример цикла в README:665-684: остановка, если `cursor` пустой или элементов меньше `count`.
- Значения `count`: по умолчанию 20 в `search_gifts` (client:364) и `SearchParams` (models:373), 50 в `get_inventory` (client:467); README-пример поиска использует `count=50` (README:674). **Ограничения `count` в коде нет** (ни проверки, ни комментария про максимум 20). Вывод: «≤ 20» по amrkt не подтверждается и не опровергается; работает ли 50 на `gifts/saling` — неизвестно.
- Активности: offset-пагинация (`offset`, `count`), client:676-702.
- Лента `/feed`: параметров пагинации нет вообще (тело `{}`).
- `total` в ответе `GiftList` (models:264).

### Имитация TLS, заголовки, прокси

- `curl_cffi` `impersonate`, по умолчанию `"chrome124"`; `""` отключает (client:65, 82-84, 94, 134-135). В докстринге заявлены `chrome99`–`chrome124`, `safari15_3`–`safari17_4_1`.
- User-Agent: если не задан — `random.choice` из 6 строк при создании клиента (client:13-20, 95); ротации между запросами **нет** — один UA на жизнь экземпляра. Набор смешан: мобильные Chrome Android 124, iOS Safari 17, CriOS, плюс усечённая строка «Macintosh … (KHTML, like Gecko)» без браузера (client:17). При `impersonate="chrome124"` UA может быть Safari/iOS — TLS-отпечаток и UA не согласованы.
- Заголовки — набор браузерного CORS-запроса из Mini App (`Origin`/`Referer` = `https://cdn.tgmrkt.io`), cookie `access_token` (см. выше).
- Прокси: один URL на всё (`http://`, `https://`, `socks5://`, `socks5h://`, `socks4://` для Pyrogram). Для `curl_cffi` логин/пароль выносятся в `proxy_auth`, порт по умолчанию 8080 (http) / 1080 (socks) (client:136-152). Для Pyrogram — словарь `scheme/hostname/port/username/password` (client:154-180). `proxy_api_only=True` — прокси только для `api.tgmrkt.io`, Telegram напрямую (client:207). Ротации прокси нет.

### Обработка ошибок, ретраи, 429

- `_request` (client:281-301): 401 → один рефреш токена и повтор; 404 → `NotFoundError`; любой другой не-200 → `APIError(status_code, response_text)`.
- **429 не обрабатывается** отдельно (попадает в `APIError`), backoff, jitter, повторов на 5xx/сетевые ошибки нет; сетевые исключения `curl_cffi` пробрасываются как есть.
- `NotForSaleError`, `InsufficientBalanceError` объявлены (exc:28-35), но **нигде не выбрасываются**; докстринг `buy_gifts` обещает `NotForSaleError` (client:444-445) — не реализовано. Тексты ошибок сервера MRKT (например, «не продаётся», «нет денег») в коде не разбираются.
- `buy_gifts`: при не-списке в ответе возвращает `[]` молча (client:449-451) — частичный/неизвестный результат покупки не различается.

### Модель данных подарка (`Gift`, models:140-258) — будущая схема ответа

Все ключи — как в JSON API (alias). Тип/дефолт — как в модели amrkt.

| JSON-ключ | Тип в amrkt | Примечание |
|---|---|---|
| `id` | str, обязательный | внутренний id MRKT; используется в buy/sell/cancel/return |
| `name` | str? | |
| `giftId` | int? | по README — Telegram gift ID |
| `giftIdString` | str? | то же строкой |
| `number` | int? | номер экземпляра |
| `title` | str? | |
| `collectionName` | str? | значение для фильтра `collectionNames` |
| `collectionTitle` | str? | |
| `giftsCollectionId` | str? | |
| `modelName` | str? | для `modelNames` |
| `modelTitle` | str? | |
| `modelRarityPerMille` | int? (0) | редкость в промилле; `/10` = % |
| `modelRarityName` | str? | |
| `modelStickerKey` | str? | |
| `modelStickerThumbnailKey` | str? | |
| `backdropName` | str? | для `backdropNames` |
| `backdropRarityPerMille` | int? (0) | |
| `backdropRarityName` | str? | |
| `backdropColorsCenterColor` | int? | цвет как int (вероятно RGB) |
| `backdropColorsEdgeColor` | int? | |
| `backdropColorsTextColor` | int? | |
| `backdropColorsSymbolColor` | int? | |
| `symbolName` | str? | для `symbolNames` |
| `symbolRarityPerMille` | int? (0) | |
| `symbolRarityName` | str? | |
| `symbolStickerKey` | str? | |
| `symbolStickerThumbnailKey` | str? | |
| `salePrice` | int (0) | nanoTON |
| `salePriceWithoutFee` | int (0) | nanoTON |
| `floorPriceNanoTONsByCollection` | int? | флор коллекции, nanoTON |
| `floorPriceNanoTONsByBackdropModel` | int? | флор по паре модель+фон, nanoTON |
| `isOnSale` | bool (false) | |
| `isOnAuction` | bool (false) | |
| `isLocked` | bool (false) | |
| `isLockedForSale` | bool (false) | |
| `isMine` | bool (false) | |
| `salesCount` | int (0) | |
| `promoteEndAt` | str? | |
| `unlockDate` | str? | даты — строки (ISO по README) |
| `nextResaleDate` | str? | |
| `nextTransferDate` | str? | |
| `receivedDate` | str? | |
| `exportDate` | str? | |
| `nextGiveAvailableAt` | str? | |
| `validateRegularGiftAt` | str? | |
| `returnLockedUntil` | str? | |
| `totalUpgradedCount` | int (0) | |
| `maxUpgradedCount` | int (0) | |
| `giftType` | str? | по README, например `"Upgraded"` |
| `luckyBuy` | bool (false) | |
| `craftable` | bool (false) | |
| `isCrafted` | bool (false) | |
| `tgCanBeCrafted` | bool (false) | |
| `minted` | bool (false) | |
| `premarketStatus` | str? | |
| `waitGiftUntil` | str? | |
| `regularGiftValidation` | str? | |
| `returnLockReason` | str? | |
| `isOnPlatform` | bool (true) | |
| `isGiveawayReceived` | bool (false) | |
| `isSpaceMonkey` | bool (false) | |
| `spaceMonkeysPoints` | int? | |

Отдельного поля «id листинга / sale id» в `Gift` нет, хотя `create_offer` требует `giftSaleId` (client:619-643) — откуда его брать, в коде не показано.

Прочие модели ответа:
- `GiftCollection` (models:271-298): `name`, `title`, `modelStickerThumbnailKey`, `createdAt`, `floorPriceNanoTons` (int, обязательный), `previousDayFloorPriceNanoTons`, `volume` (int, единицы не указаны), `isNew`, `isNewDate`, `cashbackCoef` (float?), `spiceConvertPrice`, `spaceMonkeyPoints`, `disabledCraftFrom`, `craftable`, `isHidden`, `tgCraftable`.
- `UserInfo` (`/me`, models:37-65): `id`, `accountId`, `userTonId`, `registeredAt`, `category`, `photo`, `fullName`, `refUrl`, `invitedBy`, `wallet{ton, deviceId}`, `allowsPm`, `currentLanguageCode`, `walletForPayment`, `isVIP`, `payerId`, `serverTime`, `inGameLink`, `referralRevenueCoef`, `giveawayBadge`, `channelValidationBotName`, `configs[{key, value}]`, `refCoefsDto{referralCoef, stickerReferralCoef, notGamesReferralCoef, channelReferralCoef, giftsCollectionReferralCoef, starsReferralCoef, tgPremiumReferralCoef}`, `disableWithdrawalLimit`, `disallowedSections`. `serverTime` полезен для проверки часов.

### Остальные пункты шаблона

- Оценка/флор: своего алгоритма нет; API отдаёт готовые `floorPriceNanoTONsByCollection`, `floorPriceNanoTONsByBackdropModel` в подарке и `floorPriceNanoTons`/`previousDayFloorPriceNanoTons` в коллекции.
- Комиссии: цифр в коде нет; есть только пара `salePrice`/`salePriceWithoutFee` и `cashbackCoef` у коллекции.
- Предохранители и лимиты: нет (ни throttle, ни лимитов трат, ни проверки цены перед покупкой).
- Уведомления / UI: нет.
- Хранение состояния: только файл сессии Pyrogram (`<workdir>/<session_name>.session`) — это полный доступ к Telegram-аккаунту; токен MRKT в памяти.

## Что берём

| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Таблица эндпоинтов, ключей тел и query (см. выше) | `docs/MARKETS.md#mrkt`, `markets/mrkt.py` | Формат API; переписать самим, сверить с boostNT/MRKT-API и живым ответом |
| Получение initData: `RequestAppWebView(peer=@mrkt, short_name="app", platform="android")`, вырезание `tgWebAppData` | `auth/` (Telethon) | Идея; переписать на Telethon (`messages.RequestAppWebViewRequest`) |
| Заголовки Mini App (`Origin`/`Referer` `https://cdn.tgmrkt.io`, `Authorization` без Bearer + cookie `access_token`) | `markets/mrkt.py` | Формат; проверить, какие реально нужны |
| `curl_cffi` + `impersonate`, прокси с `proxy_auth` | `markets/mrkt.py`, общий HTTP-слой | Приём; использовать `AsyncSession`, согласовать UA с профилем |
| Схема `Gift` (60 полей) и `GiftCollection` | `markets/mrkt.py` (DTO), `pricing/` | Формат ответа; все поля опциональные, кроме `id` |
| Готовые флоры `floorPriceNanoTONsByBackdropModel` / `ByCollection` / `previousDayFloorPriceNanoTons` | `pricing/` | Как дополнительный сигнал флора MRKT |
| Ленту `POST /feed` (типы `listing`/`sale`/`change_price`) | `markets/mrkt.py`, источник продаж | Формат; пагинации нет — опрос с дедупликацией по `id` |
| Деньги — `int` nanoTON везде | `pricing/`, `execution/` | Совпадает с нашим правилом |
| Рефреш токена по 401 (один повтор) | `markets/mrkt.py` | Идея; без лишнего запроса-проверки |

## Что НЕ берём и почему

- Сам пакет не ставим и не запускаем (AGENTS.md §4.3); код не копируем, хотя лицензия MIT позволила бы с указанием источника.
- Проверку токена лишним `POST /gifts/saling` перед каждым запросом — удваивает нагрузку и риск 429.
- Синхронный `curl_cffi.requests` внутри `async` — блокирует цикл; у нас `AsyncSession` с таймаутами.
- Отсутствие обработки 429/5xx, backoff, jitter, таймаутов — нарушает AGENTS.md §4.5.
- `buy_gifts` без передачи цены и без разбора ошибок — недопустимо для `execution.spend()`: нужна проверка цены непосредственно перед покупкой и статус «результат неизвестен» при нестандартном ответе.
- Случайный UA, не согласованный с TLS-профилем (Safari-UA при `chrome124`), и усечённая строка UA.
- Pyrogram — у нас Telethon.

## Открытые вопросы

- Какой баланс (`hard`/`soft`) списывается при покупке и что такое `soft` — в коде нет.
- Защищает ли `/gifts/buy` от изменения цены (передаётся ли ожидаемая цена) — в amrkt только `{"Ids": [...]}`; сверить с boostNT/MRKT-API и `tgmrkt-api`. Регистр ключа (`Ids` у buy/return vs `ids` у sale/cancel/change-price) — проверить, важен ли.
- Максимум `count` на `/gifts/saling` и `/gifts` (20 или 50) — в коде ограничения нет.
- Срок жизни токена MRKT и лимиты частоты — не найдены.
- Что значит `salePriceWithoutFee` и размер комиссии; что такое `cashbackCoef`.
- Откуда брать `giftSaleId` для `create_offer` (в `Gift` нет такого поля).
- Значения `ordering`, кроме `"Price"` и `"Date"` (README:169 упоминает только их), и формат `query`.
- Есть ли параметры у `/feed` (cursor/count/фильтры) — amrkt шлёт `{}`.
- Эндпоинты списков моделей/фонов/символов, истории продаж, вывода — в amrkt отсутствуют.

## Для MARKETS.md

Все пункты — «из кода amrkt», коммит `2a4dbf5`, на живом ответе не проверены.

- База: `https://api.tgmrkt.io/api/v1` (client:55).
- Auth: `POST /auth` `{"data": "<initData>"}` → `{"token": "..."}` (client:233-249). initData — Pyrogram `messages.RequestAppWebView(peer=@mrkt, app=InputBotAppShortName(short_name="app"), platform="android")`, строка из `tgWebAppData=` до `&tgWebAppVersion`, один `unquote` (client:217-230). Срок жизни токена — не найден; рефреш по 401.
- Заголовки: `Authorization: <token>` (без Bearer) + `Cookie: access_token=<token>`; `Origin: https://cdn.tgmrkt.io`, `Referer: https://cdn.tgmrkt.io/`, `Sec-Fetch-Site: same-site`, `Sec-Fetch-Mode: cors`, `Accept: application/json, text/plain, */*` (client:108-129). TLS: `curl_cffi impersonate="chrome124"` по умолчанию (client:65).
- Поиск: `POST /gifts/saling`, тело `{collectionNames[], modelNames[], backdropNames[], symbolNames[], ordering:"Price"|"Date", lowToHigh:bool, maxPrice:int|null, minPrice:int|null, mintable:bool|null, number:int|null, count:int, cursor:str, query:str|null, promotedFirst:bool}` → `{gifts[], total, cursor}` (models:381-398, 261-265). minPrice/maxPrice — nanoTON (client:379-380). Пагинация курсорная, первая страница `cursor:""`. Лимит count в коде не задан (дефолт 20; README-пример 50).
- Инвентарь: `POST /gifts`, то же тело (client:498).
- Карточка: `GET /gifts/gift/{id}` (client:421). Коллекции: `GET /gifts/collections` → `[{name, title, floorPriceNanoTons, previousDayFloorPriceNanoTons, volume, cashbackCoef, isHidden, ...}]` (client:431, models:271-290).
- Покупка: `POST /gifts/buy` `{"Ids": [id]}` (заглавная I, цена не передаётся) → `[{userGift: Gift, price: int}]` (client:447, models:301-304).
- Листинг: `POST /gifts/sale` `{"ids": [...], "prices": [nanoTON...]}` → `{ids, prices}` (client:557-561). Снятие: `POST /gifts/sale/cancel` `{"ids": [...]}` → `[id]` (client:578-583). Смена цены: `POST /gifts/sale/change-price` `{"ids", "prices"}` → `{ids, prices}` (client:610-614).
- Возврат в Telegram: `POST /gifts/return` `{"Ids": [...]}` (client:513).
- Баланс: `GET /balance` → `{soft, hard, totalHard, hardLocked, stars, starsFotWithdraw, spices, ...}`, деньги в nanoTON (models:68-80). Какой баланс тратит покупка — не найдено.
- Депозиты: `GET /transactions/await` → `[{id, currencyType:"Hard"|"Soft", value, softValue, receivedAt, isClaimed, isRefunded}]`; `POST /transactions/{id}` → `[{value, type, source}]` (client:334, 347).
- Профиль: `GET /me` (есть `serverTime`, `disableWithdrawalLimit`) (client:312).
- Лента: `POST /feed` `{}` → `{items: [{type: "listing"|"sale"|"change_price", id, gift: Gift, amount: nanoTON, date}]}` (client:527, models:315-334). Параметров пагинации нет.
- Офферы: `POST /offers/create` `{"price": nanoTON, "giftSaleId": str}`; `POST /offers/cancel?offerId=<id>` (query) (client:640-671). Мои активности/офферы: `GET /activities?offset=&count=&isActive=true|false` → `[{type, date, offer{id, isMine, priceNanoTONs, ownerSalePrice, gift, createdAt, endAt}}]` (client:693-702).
- Флор в подарке: `floorPriceNanoTONsByCollection`, `floorPriceNanoTONsByBackdropModel`; цены `salePrice`, `salePriceWithoutFee` — nanoTON (models:179-182).
- Ошибки: 401 → рефреш + 1 повтор; 404 → NotFound; прочее → APIError. 429/backoff/таймауты — нет (client:281-301).
- Не найдено в amrkt: WebSocket, история продаж (кроме ленты), модели/фоны/символы, вывод, офферы на коллекцию, лимиты частоты, срок жизни токена.
