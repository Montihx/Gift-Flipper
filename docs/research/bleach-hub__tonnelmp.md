# bleach-hub/tonnelmp

> Источник: исходники, клон от 2026-11-09, коммит `68064f7` (68064f70919931a5730948bb06549be15c131486). Код читался только как текст, ничего не запускалось. Живых запросов к Tonnel не было: всё ниже — «из кода (файл:строка)» или «из README». Пути ниже даны относительно корня репозитория; основной файл — `tonnelmp/marketapi.py` (далее `api.py:N` = `tonnelmp/marketapi.py:N`).

- Ссылка: https://github.com/bleach-hub/tonnelmp (PyPI: `tonnelmp`)
- Язык / стек: Python ≥3.8; `curl_cffi` (HTTP с имитацией TLS-отпечатка браузера), `pycryptodome` (AES для поля `wtf`), `fake_useragent` (случайный User-Agent). Синхронный, без async. Файлы: `tonnelmp/marketapi.py` (1458 строк), `tonnelmp/wtf.py` (33), `tonnelmp/__init__.py`, `references.txt`, `README.md`, `setup.py`, `pyproject.toml`, `LICENSE`.
- Лицензия: MIT, файл `LICENSE` («Copyright (c) 2025 bleach»), то же в `setup.py`.
- Последний коммит / активность: 2025-07-07 (`68064f7`, «added downloads badge», только README). Последнее изменение кода — 2025-06-17 (`7e3e8c1`, версия 1.2: прокси, полный набор браузерных заголовков, случайный UA). С тех пор (почти 1,5 года) кода нет — **для текущего API Tonnel считать устаревшим, всё сверять вживую**.
- Звёзды / форки / коммиты: звёзды/форки не установлено (api.github.com закрыт; в прошлой версии отчёта со слов WebFetch: 29/3, не перепроверено). Коммитов 44 (история полная: клон depth 50, упёрлись не в лимит).
- Доверие: **среднее**. Малвари не найдено: нет `exec/eval/base64`-загрузчиков, `subprocess`, отправки `authData` на сторонние адреса — все запросы только на `gifts2/gifts3.tonnel.network` и `gifts.coffin.meme` (бэкенд Tonnel). Минусы: в `wtf.py:8` **захардкожена парольная фраза** для AES (значение в отчёт не переносится; по комментарию автора — та же, что во фронтенде Tonnel); 1,5 года без обновлений; найдены баги (см. ниже); `setup.py` версии 1.0.2 при README 1.2, `fake_useragent` не в `install_requires`.

## Что делает (2–3 предложения)

Синхронная Python-обёртка над **неофициальным** веб-API маркета Tonnel (то, что дёргает фронтенд `market.tonnel.network`). Умеет: поиск листингов и аукционов с фильтрами, флоры по всем подаркам/моделям (`filterStats`), история продаж, мои подарки, покупка, листинг, снятие с продажи, разблокировка листинга, аукционы и ставки, баланс, вывод, возврат подарка в Telegram, минт, розыгрыши. Авторизация — сырой `initData`, который пользователь копирует вручную из localStorage браузера.

## Как устроено

### Хосты
- `https://gifts2.tonnel.network/api/...` — чтение: `pageGifts`, `saleHistory`, `balance/info`, `filterStats`, `giftData/{id}`, `giveaway/info` (из кода, `api.py:76,412,797,1295,1438,1204`).
- `https://gifts3.tonnel.network/api/filterStats` — только в `filterStatsPretty` (`api.py:1341`). Почему другой хост — в коде не объяснено.
- `https://gifts.coffin.meme/api/...` — все действия с деньгами и подарками: buy, list, cancel, unlock, auction, withdraw, returnGift, mint, switchTransfer, giveaway/join (из кода, `api.py:296,350,639,682,739,927,972,1018,1063,1111,1158,1260`).
- Все вызовы — `POST` с JSON-телом, даже чтение (`requests.post(...)` во всех функциях). GET в коде не найдено.

### Таблица функций (все — из кода `tonnelmp/marketapi.py`)

Общее для всех: метод POST, `Content-Type: application/json`, заголовки из `HEADERS` (`api.py:8-24`, см. «Обход защиты»), `impersonate="chrome110"`, таймаут 10 с (15 с у `withdraw` и `mintGift`), `proxies` пробрасывается. Ответ — `response.json()` без разбора; при 403/429 — исключение «Likely CloudFlare», при любом другом не-200 — исключение (повторов/backoff нет).

| Функция (строки) | URL | Тело запроса (ключи и типы, как в коде) | Ответ (что известно) |
|---|---|---|---|
| `getGifts` (`34-184`) | `https://gifts2.tonnel.network/api/pageGifts` | `filter`: **строка** JSON (`json.dumps(dict)`); `limit`: int (по умолч. 30); `page`: int (с 1); `sort`: **строка** JSON; `ref`: `0`; `user_auth`: str (initData или `""`); `price_range`: `[min, max]` или `0` (`api.py:160-172`) | список dict подарков (README:137-157, поля ниже). Авторизация не обязательна |
| `myGifts` (`186-268`) | тот же `pageGifts` | как выше; `filter` с `seller: <telegram user id>` (берётся из `user` внутри initData, `api.py:223-229`); listed: `buyer` не существует И (`price` существует ИЛИ `auction_id` существует), sort `{"message_post_time":-1,"gift_id":-1}`; unlisted: `buyer` не сущ., `refunded`≠true, `price` не сущ., sort `{"gift_num":1,"gift_id":-1}` (`api.py:231-248`) | список dict; `user_auth` обязателен |
| `getAuctions` (`473-587`) | тот же `pageGifts` | как `getGifts`; `filter` = `{"auction_id":{"$exists":true},"status":"active","asset":...}` + имя/модель/фон/символ/`gift_num` (`api.py:532-562`); сорты: `auctionEndTime:1`, `auctionStartTime:-1`, `bidHistory.amount:-1`, `bidHistory.timestamp:-1` (`api.py:520-525`) | список dict (поля аукциона в коде не разобраны) |
| `saleHistory` (`378-471`) | `https://gifts2.tonnel.network/api/saleHistory` | `authData`: str; `page`: int; `limit`: int (по умолч. 50); `type`: `"ALL"\|"SALE"\|"INTERNAL_SALE"\|"BID"`; `filter`: **объект** (не строка!) с `gift_name`/`model`/`backdrop`; `sort`: **объект** (`json.loads`), по умолч. `{"timestamp":-1,"gift_id":-1}` (`api.py:453-460`) | «список» (докстринг); поля ответа в коде и README не описаны |
| `buyGift` (`707-773`) | `https://gifts.coffin.meme/api/buyGift/{gift_id}` (gift_id в пути) | `authData`: str; `asset`: `"TON"`; `price`: **float** (`float(price)`, TON, цена листинга без 10%); `timestamp`: str (unix-секунды); `wtf`: str (см. ниже); опционально при `receiver`: `receiver` (Telegram user id), `anonymously`: bool, `showPrice`: bool (`api.py:749-762`) | dict «success или error» (докстринг); поля не описаны |
| `listForSale` (`270-324`) | `https://gifts.coffin.meme/api/listForSale` | `authData`: str; `gift_id`: int (Tonnel id, не `gift_num`); `price`: int\|float как передали (без приведения); `asset`: `"TON"`; `timestamp`; `wtf` (`api.py:306-313`) | dict status success/error |
| `cancelSale` (`326-376`) | `https://gifts.coffin.meme/api/cancelSale` | `authData`; `gift_id`: int; `timestamp`; `wtf` (`api.py:360-365`) | dict status |
| `changePrice` | **в коде не найдено**. Отдельного эндпоинта нет; вероятно, смена цены = `cancelSale` + `listForSale` (не проверено) | — | — |
| `unlockListing` (`1137-1181`) | `https://gifts.coffin.meme/api/unlock` | `authData`; **`sale_id`**: int (в него кладётся аргумент `gift_id`) (`api.py:1166-1169`) | dict. README:323-325: стоит 0.1 TON, нужен если у подарка `limited: true`. **Не экспортирована** в `__init__.py` |
| `returnGift` (`953-995`) | `https://gifts.coffin.meme/api/returnGift` | `gift_id`: int; `authData` (`api.py:980-983`). `timestamp/wtf` нет | dict. README:358 — «Not tested yet». Особая обработка только 429 (403 → общее исключение) |
| `withdraw` (`896-951`) | `https://gifts.coffin.meme/api/balance/withdraw` | `wallet`: str (TON-адрес); `authData`; `amount`: **float**; `asset`: `"TON"\|"USDT"\|"TONNEL"` (`api.py:935-940`) | dict. Докстринг (`api.py:910`): `amount ≥ 0.5`, комиссия 0.001 «вычитается внутри» (не проверено) |
| `info` (баланс) (`776-819`) | `https://gifts2.tonnel.network/api/balance/info` | `authData` (`api.py:805-807`) | по README:198-208: `status`, `balance` (TON, float), `memo`, `transferGift` (bool; false = «внутренняя покупка»), `usdtBalance`, `tonnelBalance`, `referrer`, `photo_url`, `name` |
| `switchTransfer` (`1044-1085`) | `https://gifts.coffin.meme/api/user/switchTransfer` | `transferGift`: bool; `authData` (`api.py:1071-1074`) | dict. Это **не** передача подарка, а переключатель режима «внутренняя покупка» (купленный подарок остаётся на балансе Tonnel vs. сразу отправляется в Telegram — по смыслу README:36,202; точная семантика не проверена) |
| `transferGift` (как функция) | **в коде не найдено**. Есть только поле `transferGift` в `info` и `switchTransfer` | — | — |
| `filterStats` (`1278-1315`) | `https://gifts2.tonnel.network/api/filterStats` | `authData` (`api.py:1303-1305`) | `{"status":"success", "data": {"<Gift>_<Model (r%)>": {"floorPrice": число, "howMany": int}}}` — ключи из разбора в `api.py:1368-1387`; флор «raw, без 10%» (README:477) |
| `filterStatsPretty` (`1319-1412`) | `https://gifts3.tonnel.network/api/filterStats` | `authData` | локальная перегруппировка: `data[gift_lower][model_lower] = {floorPrice, howMany, rarity}` + `data[gift]["data"]` = min флор и сумма `howMany` по коллекции (`api.py:1368-1407`) |
| `giftData` (`1414-1458`) | `https://gifts2.tonnel.network/api/giftData/{gift_id}` | `authData`; `ref`: `""` (`api.py:1446-1449`) | **баг: нет `return`** — функция всегда возвращает `None`. По README:488 при `gift_id` < 0 (бандл) приходит ещё `bundleData` |
| `createAuction` (`593-657`) | `https://gifts.coffin.meme/api/auction/create` | `authData`; `gift_id`; `startingBid`: int\|float; `auctionEndTime`: ISO-строка UTC с мс и `Z` (now + 1/2/3/6/12/24 ч) (`api.py:620-637`) | dict |
| `cancelAuction` (`659-705`) | `https://gifts.coffin.meme/api/auction/cancel` | `authData`; `auction_id`: str (`api.py:690-693`) | dict |
| `placeBid` (`997-1042`) | `https://gifts.coffin.meme/api/auction/bid` | `authData`; `auction_id`: str; `amount`: float; `asset`: str (`api.py:1026-1031`) | dict. README:432 — «Not tested yet» |
| `mintGift` (`1087-1135`) | `https://gifts.coffin.meme/api/mint/start` | `authData`; `wallet`: str; `gift_id` (`api.py:1119-1123`) | dict. README:372: стоит 0.3 TON, «Not tested yet» |
| `giveawayInfo` (`1183-1226`) | `https://gifts2.tonnel.network/api/giveaway/info` | `giveAwayId`: str; `authData` | dict |
| `joinGiveaway` (`1228-1276`) | `https://gifts.coffin.meme/api/giveaway/join` | `authData`; `giveAwayId`; `timestamp`; `wtf`; опц. `ticketCount`: int (`api.py:1250-1258`) | dict |

Важное по полям тела:
- Авторизация называется по-разному: `user_auth` только в `pageGifts` (getGifts/myGifts/getAuctions), во всех остальных — `authData` (из кода).
- В `pageGifts` `filter` и `sort` — **JSON-строки**; в `saleHistory` — **объекты**. Легко ошибиться.
- `gift_num` в фильтре передаётся строкой (`str(gift_num)`, `api.py:158`).

### Фильтр поиска (`pageGifts`), из кода `api.py:102-158` и `references.txt`
- База: `price` существует, `buyer` не существует, `asset` = `TON|USDT|TONNEL`.
- Обычный режим (без флагов): + `refunded` ≠ true, `export_at` существует (`api.py:128-130`). Это совпадает с «default filter» в `references.txt:52`.
- `premarket=True` → `premarket: true`; `telegramMarketplace=True` → `telegramMarketplace: true` и `export_at` не существует; `mintable=True` → `export_at < now (ISO UTC)`; `bundle=True` → `gift_id < 0` (бандлы имеют отрицательный id) (`api.py:108-126`).
- `gift_name` — точное значение в Title Case (особый случай `Jack-in-the-Box`, `api.py:133-136`).
- `model` / `backdrop` / `symbol`: без процента → `{"$regex": "^Name \\("}`; с процентом → точная строка `"Name (1.5%)"` (`api.py:138-155`). Т.е. значения атрибутов в БД хранятся как `"Имя (редкость%)"`.
- Сортировки (`api.py:84-95`): `price ±1`, `message_post_time:-1` (новые), `export_at:1` (время минта), `rarity:-1`, `gift_num ±1`, `modelRarity:1`, `backdropRarity:1`, `symbolRarity:1`; всегда вторым ключом `gift_id:-1`.
- Пагинация: `page` с 1, `limit` по умолчанию и максимум 30 (README:272 «as far as i know»); у `saleHistory` максимум 50 (README:340).

### Авторизация
- `authData` = значение ключа **`web-initData`** из localStorage `https://market.tonnel.network/` (README:48-50), т.е. сырой Telegram WebApp `initData` (query-строка `query_id=...&user=...&auth_date=...&hash=...`). Подтверждение в коде: `myGifts` разбирает его `urllib.parse.parse_qs`, берёт `user` → JSON → `id` (`api.py:223-229`).
- Передаётся **в теле** JSON (`authData` / `user_auth`), а не в заголовке. Cookies и Bearer-токенов нет (из кода).
- Программного получения initData (Pyrogram/Telethon `RequestWebView`) **в коде нет** — только ручное копирование. Срок жизни initData в коде/README не указан.

### `wtf.py` — что это
Это **не подпись запроса**, а анти-бот/анти-replay токен времени, повторяющий `CryptoJS.AES.encrypt(timestamp, passphrase)` фронтенда (комментарий автора `wtf.py:10-13`: «equivalent to cryptojs freeman used in the backend … basically encrypts the timestamp and thats it»). Алгоритм (`wtf.py:15-33`), словами:
1. `timestamp` = текущее unix-время в секундах, строкой.
2. Случайная 8-байтная соль.
3. Ключ (32 байта) и IV (16 байт) выводятся из **захардкоженной парольной фразы** + соль по схеме OpenSSL `EVP_BytesToKey` (MD5, 1 итерация: `D_i = MD5(D_{i-1} || pass || salt)`, склеивать до 48 байт).
4. AES-256-CBC, паддинг PKCS#7, шифруется только строка `timestamp`.
5. `wtf` = base64(`"Salted__"` + соль + шифртекст) — стандартный формат CryptoJS/OpenSSL.
6. В тело кладутся оба поля: `timestamp` (открыто) и `wtf`.

Используется только в `buyGift`, `listForSale`, `cancelSale`, `joinGiveaway`. Не используется в `withdraw`, `returnGift`, `unlock`, `createAuction`, `cancelAuction`, `placeBid`, `mintGift`, `switchTransfer` (из кода). Токен **не привязан** к `gift_id`/`price`/пользователю — только к времени; допустимое окно по времени на сервере неизвестно. Парольная фраза — секрет фронтенда Tonnel, в отчёт не переносится; для своего клиента её придётся извлечь из текущего JS-бандла сайта самим и быть готовыми к её смене.

### Модель данных подарка
Из README (пример ответа `getGifts`, README:137-186) и класса `Gift` (`api.py:821-894`):
`gift_num` (номер в Telegram, int), `gift_id` (внутренний id Tonnel, int; < 0 — бандл), `name` (название коллекции; **в фильтре это `gift_name`**, в ответе — `name`), `model`, `backdrop`, `symbol` (строки вида `"Zebra (1.5%)"`), `price` (float, TON, **без 10%**), `asset`, `status` (`forsale` / аукцион), `limited` (true → нужен `unlockListing`), `auction` (None или dict), `export_at` (ISO, когда подарок можно минтить), `customEmojiId`, `availabilityIssued`, `availabilityTotal`, `backdropData`, `message_in_channel`, `premarket` (bool), `bundleData` (только у бандлов). Из сортировок/фильтров видны ещё служебные поля `message_post_time`, `refunded`, `buyer`, `seller`, `rarity`, `modelRarity`, `backdropRarity`, `symbolRarity`, `telegramMarketplace`, `auction_id`, `auctionEndTime`, `bidHistory[].amount/.timestamp` — в ответе не подтверждены.

### Оценка/флор
Своего алгоритма нет. Флор берётся готовым из `filterStats` (сервер Tonnel отдаёт `floorPrice` и `howMany` по каждой паре «коллекция_модель (редкость%)»). `filterStatsPretty` лишь группирует и считает флор коллекции как минимум по моделям (`api.py:1396-1401`). Альтернатива — `getGifts(sort="price_asc", limit=1)` (README:493-499). Флора по фону/символу в `filterStats` нет (ключ только gift_model).

### Комиссии и единицы цены
- Единицы: **TON дробным числом** (float), не nano. `buyGift` шлёт `float(price)` (`api.py:752`), `withdraw`/`placeBid` — `float(amount)`; `listForSale` шлёт `price` как есть (int или float) (`api.py:309`). Никакого округления в коде нет.
- 10% комиссия покупки: **в коде не умножается** (поиск `1.1`/`*1.1` — пусто). По README:399 и 506 `buyGift` принимает «сырую» цену листинга, а Tonnel сам списывает `price * 1.1`. То есть `price` в листинге/`filterStats` — без комиссии, реальная стоимость покупки = `price × 1.1` (из README, не проверено). Как сервер округляет 10% — неизвестно.
- Комиссия продавца при `listForSale` — в коде и README не найдено.
- Прочие цифры (только README/докстринги, не проверены): unlock 0.1 TON (README:323), mint 0.3 TON (README:372), вывод: минимум 0.5, комиссия 0.001 (`api.py:910`).

### Обход защиты
- TLS: `curl_cffi` с `impersonate="chrome110"` во всех 21 вызовах (из кода). Менялся только набор заголовков, профиль chrome110 был с самого начала.
- Заголовки (`api.py:8-24`), общие для всех хостов: `authority` (подставляется хост — `gifts2.tonnel.network` / `gifts3...` / `gifts.coffin.meme`), `accept: */*`, `accept-encoding: gzip, deflate, br, zstd`, `accept-language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7`, `content-type: application/json`, **`origin: https://market.tonnel.network`**, `priority: u=1, i`, **`referer: https://market.tonnel.network/`**, `sec-ch-ua: "Google Chrome";v="137", ...`, `sec-ch-ua-mobile: ?0`, `sec-ch-ua-platform: "Windows"`, `sec-fetch-dest: empty`, `sec-fetch-mode: cors`, `sec-fetch-site: same-site`, **`user-agent`: случайный из `fake_useragent`** на каждый вызов.
- Cookies (в т.ч. `cf_clearance`) — **не используются** (в коде не найдено).
- История (git): до 1.1.3 был только `User-Agent: Mozilla/5.0`; в 1.1.3 (`dcc2cda`, 2025-06-12) добавлены `Origin`/`Referer`/UA Chrome 135 — «Fixed 403»; в 1.2 (`7e3e8c1`, 2025-06-17) — полный набор заголовков из boostNT/Tonnel-API, случайный UA и прокси — «Another 403 fix … 403 should now appear less often» (README:107-121). Т.е. 403 от Cloudflare бывали и после фикса.
- Несостыковки, которые сами могут быть сигналом бота: TLS-отпечаток Chrome 110 + `sec-ch-ua` Chrome 137 + случайный UA (может оказаться Firefox/Safari/мобильным); `sec-fetch-site: same-site` уходит и на `gifts.coffin.meme`, который не same-site с `market.tonnel.network`; `authority` отправляется как обычный заголовок (в HTTP/2 это псевдозаголовок). Глобальный `HEADERS` мутируется в каждом вызове — не потокобезопасно.

### WebSocket
Упоминаний нет (поиск `websocket`/`wss`/`socket` по репо и истории — пусто). Только polling `POST pageGifts`.

### `references.txt`
Личные заметки автора по `pageGifts`: список полей тела (`filter, limit, page, price_range, ref: 0, sort, user_auth`), 10 вариантов сортировки с пояснениями, примеры regex-фильтров по `backdrop`/`symbol`/`model` («первая буква заглавная»), «default filter» и фильтры для listed/unlisted «моих подарков». В примерах захардкожен реальный Telegram ID продавца (значение не переносим). Новой информации сверх кода нет; подтверждает, что фильтр по узору называется `symbol`.

### Предохранители и лимиты
Нет: ни throttle, ни retry/backoff, ни проверки цены перед покупкой, ни DRY_RUN. Таймауты 10/15 с. Ошибки 403/429 → исключение с текстом «Likely CloudFlare». Тело ответа при ошибке не возвращается (убрано в 1.0.4.1 «trashes out logging», README:70), кроме `giveawayInfo`/`joinGiveaway`/`filterStats*`, где `response.text` попадает в исключение.

### Уведомления / UI, хранение состояния
Нет (библиотека без состояния).

### Найденные баги (из кода)
- `giftData` не возвращает результат (`api.py:1450-1458` — нет `return`).
- `unlockListing` не экспортирована в `tonnelmp/__init__.py` (хотя описана в README).
- `setup.py` — `version="1.0.2"`, нет `fake_useragent` в `install_requires`, хотя `marketapi.py:6` его импортирует.
- `import re` стоит в середине файла (`api.py:1317`), а используется выше в `tonneltitle` (`api.py:27`) — работает только потому, что модуль загружается целиком до вызова.
- README:466 пишет ключ `floorprice`, код читает `floorPrice` (`api.py:1386`) — верить коду.

## Что берём
| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Схема эндпоинтов (хосты gifts2/gifts3/coffin.meme, пути, тела) | `docs/MARKETS.md#tonnel`, `markets/tonnel.py` | формат API, переписать самим; перед использованием сверить с живым трафиком сайта (код 1,5 года без обновлений) |
| Фильтр `pageGifts` (база + флаги premarket/telegramMarketplace/mintable/bundle, regex `^Name \(`) и сорты | `markets/tonnel.py` | переписать; `filter`/`sort` слать JSON-строками |
| `filterStats` как источник флоров по модели одним запросом | `markets/tonnel.py`, `pricing/floor.py` | вместо десятков `pageGifts`; флор без 10% |
| `saleHistory` с `type` (SALE/INTERNAL_SALE/BID) | `pricing/sales.py` | источник продаж Tonnel для проверки 24ч; формат ответа снять фикстурой |
| Покупка `buyGift/{gift_id}` с `price` = цена листинга, `timestamp`+`wtf` | `markets/tonnel.py` (только через `execution.spend()`) | переписать; учитывать итог = price×1.1 в `pricing/fees.py` |
| Алгоритм `wtf` (CryptoJS-совместимый AES-256-CBC + EVP_BytesToKey/MD5 над timestamp) | `markets/tonnel.py` | переписать по описанию; парольную фразу брать из актуального фронтенда и держать в конфиге, не в коде |
| Заголовки браузера + curl_cffi impersonate + прокси | `markets/tonnel.py` | идея; согласовать UA, `sec-ch-ua` и профиль impersonate между собой (одна версия Chrome), без случайного UA |
| `myGifts` через `pageGifts` с `seller = user.id из initData` | `markets/tonnel.py` | формат API |
| `unlockListing` (`sale_id`), `limited: true` у подарка | `markets/tonnel.py`, `execution/` | учесть 0.1 TON в расчёте при перепродаже (не проверено) |

## Что НЕ берём и почему
- Код целиком (хоть и MIT): синхронный, глобальные мутируемые заголовки, нет ретраев/лимитов, баги, захардкоженный секрет фронтенда.
- Случайный `fake_useragent` на каждый запрос: рассогласует UA с TLS-отпечатком и `sec-ch-ua`.
- Аукционы, розыгрыши, минт — не MVP.
- Ручное копирование `web-initData` — у нас initData получаем через Telethon (`RequestWebView`) автоматически.

## Открытые вопросы
- Актуальны ли хосты (`gifts2/gifts3.tonnel.network`, `gifts.coffin.meme`), пути и парольная фраза `wtf` сейчас (последний код — 2025-06-17).
- Окно допустимого `timestamp` для `wtf`; что сервер отвечает на устаревший/неверный `wtf`.
- Формат ответов `buyGift`/`listForSale`/`cancelSale` (успех и ошибки), `saleHistory`, `getAuctions` — в коде не описаны, снять фикстуры.
- Как сервер считает и округляет +10% при покупке; есть ли комиссия продавца; проверить на малой покупке.
- Как менять цену листинга (нет `changePrice`): cancel+list или есть отдельный путь.
- Срок жизни `initData` для Tonnel; принимает ли сервер initData, полученный через Telethon для бота Tonnel, наравне с `web-initData`.
- Лимиты запросов и условия 403 Cloudflare; нужен ли `cf_clearance`.
- WebSocket событий Tonnel — здесь нет; искать в topcvetok/telegram-gift-watch (задание A).
- Что именно делает `switchTransfer`/`transferGift` (куда попадает купленный подарок).

## Для MARKETS.md
Tonnel (источник: bleach-hub/tonnelmp `68064f7`, код последний раз менялся 2025-06-17; живых проверок не было):
- Транспорт: все вызовы `POST`, JSON, `curl_cffi impersonate="chrome110"`; заголовки `Origin: https://market.tonnel.network`, `Referer: https://market.tonnel.network/`, `sec-fetch-*`, `sec-ch-ua` (Chrome 137), UA; cookies нет (из кода `marketapi.py:8-24`).
- Авторизация: сырой `initData` (`web-initData` из localStorage) в теле: `user_auth` в `pageGifts`, `authData` в остальных (из кода + README:48-50).
- Поиск: `POST https://gifts2.tonnel.network/api/pageGifts` `{filter: str(JSON), sort: str(JSON), page: int≥1, limit: int≤30, price_range: [min,max]|0, ref: 0, user_auth: str}` → список подарков (из кода `marketapi.py:160-175`).
- Фильтр по умолчанию: `{"price":{"$exists":true},"buyer":{"$exists":false},"refunded":{"$ne":true},"export_at":{"$exists":true},"asset":"TON"}`; атрибуты `model/backdrop/symbol` как `"Name (r%)"` или `{"$regex":"^Name \\("}`; бандлы `gift_id<0` (из кода `marketapi.py:102-158`).
- Флоры: `POST https://gifts2.tonnel.network/api/filterStats` `{authData}` → `{status, data:{"Gift_Model (r%)":{floorPrice, howMany}}}`, флор без 10% (из кода `marketapi.py:1295,1368-1387` + README:477).
- История продаж: `POST https://gifts2.tonnel.network/api/saleHistory` `{authData, page, limit≤50, type: ALL|SALE|INTERNAL_SALE|BID, filter: obj, sort: obj}` (из кода `marketapi.py:453-460`).
- Баланс: `POST https://gifts2.tonnel.network/api/balance/info` `{authData}` → `balance, usdtBalance, tonnelBalance, memo, transferGift, ...` (код + README:198-208).
- Покупка: `POST https://gifts.coffin.meme/api/buyGift/{gift_id}` `{authData, asset:"TON", price: float TON (цена листинга без 10%), timestamp: str unix-сек, wtf: str}`; списывается price×1.1 (код `marketapi.py:739-762`; 10% — только README:399,506).
- Листинг: `POST https://gifts.coffin.meme/api/listForSale` `{authData, gift_id:int, price: TON, asset:"TON", timestamp, wtf}`; снятие: `POST .../api/cancelSale` `{authData, gift_id, timestamp, wtf}`; changePrice — нет (из кода).
- Разблокировка листинга: `POST https://gifts.coffin.meme/api/unlock` `{authData, sale_id}` (0.1 TON — README); возврат в Telegram: `POST .../api/returnGift` `{gift_id, authData}`; вывод: `POST .../api/balance/withdraw` `{wallet, authData, amount: float, asset}` (min 0.5, fee 0.001 — докстринг).
- `wtf` = CryptoJS AES-256-CBC (ключ/IV через EVP_BytesToKey-MD5 от парольной фразы фронтенда + 8-байтной соли) над строкой unix-timestamp, base64 `Salted__`+salt+ct; только в buy/list/cancel/giveaway-join (из кода `wtf.py:15-33`).
- Единицы: TON float, не nano; округления в коде нет.
- WebSocket: не упоминается (из кода).
- Защита: 403/429 = «Likely CloudFlare»; несколько «403 fix» в changelog (README:107-121).
