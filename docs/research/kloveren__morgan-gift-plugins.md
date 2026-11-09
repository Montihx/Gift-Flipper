# kloveren/morgan-gift-plugins

Источник: исходники, клон от 2026-11-09, коммит `37637ebc16141e06bc10feb2ed0ee17a61f4fbdd`. Живых запросов к API не было. Все пути ниже относительны к корню репозитория.

- Ссылка: https://github.com/kloveren/morgan-gift-plugins
- Язык / стек: Node.js (ESM), плагины для фреймворка Teleton (TONresistor/teleton-agent). Каждый плагин: `index.js` + `manifest.json` (+ иногда `README.md`). `package.json` в репозитории нет. Зависимости берутся из окружения Teleton: `@ton/core`, `@ton/ton`, `@ton/crypto`, опционально `@orbs-network/ton-access` (`plugins/marketapp/index.js:15-18`, `:98`).
- Лицензия: MIT, «Copyright (c) 2025-2026 Kloveren» (`LICENSE`). Плагины `dyor`, `geckoterminal` и `invoices` в манифестах подписаны автором «teleton (TONresistor)», `repository: TONresistor/teleton-plugins`, то есть это чужой код (тоже MIT).
- Последний коммит / активность: 2026-03-27 (`eea236f` «chore: sync plugin versions, add CI, fix docs» и merge PR #1 `37637eb`). Предыдущая активность: 2026-02-22…24. С конца марта 2026 коммитов нет.
- Звёзды / форки / коммиты: звёзды и форки не установлены. Коммитов 15, это вся история (клон не неглубокий, `.git/shallow` нет).
- CI: `.github/workflows/ci.yml`, запускается на push и PR. Делает только `node --check plugins/*/index.js` (проверка синтаксиса) и `python3 -m json.tool` для каждого `manifest.json`. Тестов нет.
- Доверие: среднее. Признаков малвари нет: обфускации, `eval`/`new Function`/`child_process` нет, бинарников нет. Все внешние хосты легитимные: giftstat, getgems, marketapp, fragment, toncenter, tonapi, quickchart, dyor, geckoterminal. Но у торговых плагинов есть риск: они подписывают «вслепую» транзакции, которые вернул сервер маркета (см. «Предохранители»). Мнемоника лежит открытым текстом в `~/.teleton/wallet.json`.

## Что делает (2–3 предложения)
Это 9 плагинов-инструментов для LLM-агента @morgan_agent по рынку подарков Telegram на TON. Они дают аналитику (Giftstat, GetGems, MarketApp, Fragment), сравнение флоров между площадками, «отслеживание китов», детектор аномалий, графики и торговые действия (купить, выставить, сменить цену, снять с продажи) на GetGems и MarketApp с подписью из кошелька агента. Off-chain-маркеты Portals, Tonnel и MRKT напрямую **не опрашиваются**: их флоры берутся только через агрегатор Giftstat.

## Как устроено

### Источник данных
Везде polling по запросу инструмента. WebSocket нет. Плагин `whale-analytics` по умолчанию раз в 24 часа сам делает снапшот (`plugins/whale-analytics/index.js:60-65`).

#### 1. `gift-price-compare`: «6 площадок» и что на самом деле опрашивается
README и манифест заявляют 6 площадок: on-chain GetGems, MarketApp, Fragment; off-chain Portals, Tonnel, MRKT. Это из README и `plugins/gift-price-compare/manifest.json`. **В коде** напрямую опрашиваются только 4 источника (`plugins/gift-price-compare/index.js:408-413`):

| Источник | Как | URL / метод / параметры | Единицы цены | Код |
|---|---|---|---|---|
| Giftstat (агрегатор; даёт разбивку по маркетам, в т.ч. Portals и Tonnel) | GET ×2 параллельно, без авторизации | `https://api.giftstat.app/current/collections/floor?marketplace=all&limit=300` и `https://api.giftstat.app/current/collections/models/floor?limit=5000` | `floor_price` используется как есть, без деления, т.е. TON | `:57-99` |
| MarketApp | GET, заголовок `Authorization: <token>` (сырой токен, без `Bearer`), `Accept: application/json` | `https://api.marketapp.ws/v1/gifts/onsale/?collection_address=<EQ…>&sort_by=min_bid_asc[&model=<имя>]`; берутся первые 10 `items` | `item.min_bid` в nanoTON (/1e9), иначе `Object.values(item.status)[0].price_nano` в nanoTON | `:101-152` |
| MarketApp (справочник коллекций) | GET, тот же заголовок | `https://api.marketapp.ws/v1/collections/gifts/`: массив `{name, address, ...}` | — | `:154-167` |
| GetGems | POST GraphQL, `Content-Type: application/json`, опционально `X-Api-Key` | `https://api.getgems.io/graphql`, запрос `nftCollectionByAddress(address){name approximateItemsCount floorPrice nftItems(first:5, filter:{saleType:ON_SALE, attributes:[{traitType:"Model",value}]}, sort:PRICE_ASC){items{name address sale{fullPrice} attributes{traitType value}}}}` | `floorPrice` и `sale.fullPrice` в nanoTON (/1e9) | `:169-229` |
| Fragment | Скрейпинг HTML/AJAX | 1) GET `https://fragment.com/`: из `Set-Cookie` берётся `stel_ssid`, из HTML regex-ом `hash=([a-f0-9]+)`. 2) GET `https://fragment.com/gifts` с `X-Requested-With: XMLHttpRequest`, `Cookie: stel_ssid=…`, в ответе JSON с HTML-списком коллекций в поле `h`. 3) POST `https://fragment.com/api?hash=<hash>`, form-urlencoded: `method=searchAuctions&type=gifts&query=&sort=price_asc&filter=sale&view=list&collection=<slug>`, ответ `{ok, html}`, строки `<tr>` разбираются regex-ами | Строка TON из `icon-before icon-ton">…<` → `parseFloat` | `:231-344` |

Portals, Tonnel и MRKT не опрашиваются: в `gift-price-compare` нет ни их URL, ни клиентов. Они попадают в сравнение только как ключи `marketplace`, которые вернул Giftstat (`:424-432`). Возвращает ли Giftstat `mrkt` в `/current/collections/floor?marketplace=all`, в коде не видно. В описании `giftstat` значение `marketplace` ограничено enum `portals, tonnel, fragment, getgems` (`plugins/giftstat/index.js:141`).

Таймаут на каждый запрос 12 с (`:53-55`). Ретраев и троттлинга в этом плагине нет. Ошибка любого источника превращается в `null` и молча пропускается.

#### 2. `giftstat`: агрегатор флоров
Всё ниже из кода `plugins/giftstat/index.js`. Авторизации нет: комментарий в `:10` и `fetch` без заголовков в `:33`. Таймаут 15 с. Ретраев и троттлинга нет. README плагина даёт для `limit` значение по умолчанию 200 (у `thematics/lines` 10000), документация: `wiki.giftstat.app`.

Базы: v1 `https://api.giftstat.app` (`:21`), v2 `https://apiv2.giftstat.app` (`:22`). Все запросы GET с query-параметрами.

| Путь | Параметры | Поля ответа, которые читает код (где) |
|---|---|---|
| v1 `/current/collections` | `fields`, `limit`, `offset` | `data[]`: `blockchain_address`/`address`, `collection_slug`/`slug`/`collection`, `total_amount` (`plugins/whale-analytics/index.js:149-155`) |
| v1 `/current/collections/floor` | `marketplace` = `portals` (по умолч.) / `tonnel` / `fragment` / `getgems`; в compare и whale передаётся `all`; `limit`, `offset` | `data[]`: `slug`, `collection`, `marketplace`, `floor_price` (`gift-price-compare/index.js:70-79`, `whale-analytics/index.js:168-176`) |
| v1 `/current/collections/models` | `limit`, `offset` | в коде не разбирается |
| v1 `/current/collections/models/stat` | `limit`, `offset` | не разбирается (по описанию: count, total amount, rarity, market share) |
| v1 `/current/collections/models/floor` | `limit`, `offset` (в compare `limit=5000`) | `data[]`: `collection_slug`, `model`, `floor_price` (`gift-price-compare/index.js:87-92`) |
| v1 `/current/collections/backdrops`, `/current/collections/symbols` | `limit`, `offset` | не разбирается |
| v1 `/current/thematics`, `/current/thematics/lines` | — / `limit`, `offset` | не разбирается |
| v1 `/current/ton-rate` | — | не разбирается (курс TON/USDT) |
| v1 `/history/collections/floor` | `marketplace` (`portals`/`tonnel`/`getgems`), `scale` (`day`/`hour`), `days`, `limit`, `offset` | `data[]`: `slug`/`collection`, `date`/`timestamp`, `floor_price`/`floor`, `volume`/`total_volume`, `trades`/`total_trades`, `avg_price` (`whale-analytics/index.js:694-707`). Видно по цепочкам fallback-ов, что точная схема автору неизвестна |
| v2 `/history/index/floor` | параметров нет, `days` фильтруется на клиенте | подсказка в коде: `price`, `upper_threshhold`, `lower_threshhold` (так, с опечаткой), `dt`; интервал ~30 мин, данные с ноября 2025 (`giftstat/index.js:345`, `:387`) |
| v2 `/history/collections/floor` | `limit` (по умолч. 1000), `offset`; клиент листает до 10 страниц | подсказка «Typically includes: collection/name, dt/date, floor_price, tonnel_floor_price, portals_floor_price, mrkt_floor_price» (`:473`). Это текст-подсказка для LLM, кодом не проверяется |

Вывод о резервном источнике флоров: **подходит как резервный и сверочный источник** флора коллекции и модели (публичный, без ключа, есть разбивка по маркетам и история). Ограничения: (а) флор только по коллекции и модели, без фона и символа; (б) частота обновления в коде не указана (у индекса ~30 мин, по подсказке); (в) единицы `floor_price` по коду, видимо, TON (без конвертации), но явно нигде не задокументированы; (г) нет rate-limit в коде и нет данных о лимитах сервиса. Для реальных решений о покупке не годится, только для sanity-check и fallback.

#### 3. `whale-analytics` (инструмент `whale_tracker`)
- Данные о сделках:
  - GetGems REST: GET `https://api.getgems.io/public-api/v1/nfts/history/gifts?limit=100&types[]=sold[&after=<cursor>]`, заголовок `Authorization: <GETGEMS_API_KEY>`. Без ключа источник считается заблокированным (`plugins/whale-analytics/index.js:107-139`). Используемые поля: `items[]` с `collectionAddress`/`collection.address`, `address`, `name`, `typeData.priceNano` (nanoTON) / `typeData.price`, `typeData.newOwner` (покупатель), `typeData.oldOwner` (продавец), `time` (unix-сек.); курсор `cursor`. Фильтр по коллекции на клиенте (сравнение raw-адресов), до 5 страниц × 100 (`:183-236`).
  - MarketApp: GET `https://api.marketapp.ws/v1/gifts/history/?collection_address=<EQ…>&limit<=100`, `Authorization: <token>`. Поля: `type_details.price_nano`/`price`, `type_details.dst` (покупатель), `type_details.src` (продавец), `ts`/`timestamp`/`date` (`:238-295`).
  - Giftstat: флоры только для оценки (`:161-181`).
- Дедупликация по ключу `nft_address:buyer:time` (`:311-321`). Период по умолчанию 14 дней, максимум 30, top_n = 10 (`:481-483`).
- **Классификация.** Меток «Diamond Hands / Flipper / Accumulator» в коде нет: они есть только в корневом `README.md:28`. Реальная логика (`plugins/whale-analytics/index.js:352-364`), где `buy` и `sell` = число покупок и продаж кошелька за период:

```js
const totalTrades = stats.count + sellCount;
if (totalTrades < 3)                                   strategy = "insufficient_data";
else if (stats.count > sellCount * 3)                  strategy = "accumulating";
else if (sellCount > stats.count * 2)                  strategy = "distributing";
else if (Math.abs(stats.count - sellCount) < stats.count * 0.3) strategy = "trading";
else                                                   strategy = "mixed";
```
  То есть: `buy+sell < 3` → недостаточно данных; `buy > 3·sell` → накопитель («Accumulator»); `sell > 2·buy` → распродаёт; `|buy−sell| < 0.3·buy` → трейдер («Flipper»). Аналога «Diamond Hands» нет. «Киты» — это топ по **числу покупок** за период (`:345-347`), а не держатели: реальные балансы и владение не запрашиваются. Это выборка из последних продаж (до 300 на коллекцию и источник), что признано в описании (`:448`).
- Снапшоты хранятся в SQLite, таблица `whale_snapshots(snapshot_date, collection, wallet_address, bought_count, sold_count, net_accumulation, bought_volume_ton, sold_volume_ton, strategy, floor_ton)`, UNIQUE по (дата, коллекция, кошелёк) (`:68-91`).
- Если GetGems трижды подряд вернул пусто, он пропускается; повторная проверка через 6 ч (`:1135-1136`).
- `anomaly_detector` (`:713-800`) работает на дневной истории флоров Giftstat (по умолчанию marketplace=portals). Z-score по выборочному σ, порог `sensitivity` = 2.5. Правила:
  - объём-спайк + флор-спайк + на следующий день флор вернулся (|next−prev|/prev < 0.15) → `wash_trading` (high);
  - объём + флор без возврата → `organic_demand`;
  - только объём → `volume_spike`;
  - флор вверх → `price_pump` (high, если ×>3);
  - флор вниз → `price_dump` (high, если ×<0.5).

### Сопоставление коллекций между площадками (алиасы)
Таблица `COLLECTION_ALIASES` (`plugins/gift-price-compare/index.js:15-27`, дубль в `plugins/whale-analytics/index.js:29-41`). Ключ — on-chain адрес коллекции (EQ…), значение — варианты имени. Всего 11 коллекций:

| Адрес коллекции | Алиасы |
|---|---|
| EQDLM65t0shS7gZAg0lMltGHYhsU94PzsMJHhYibmRV7kdUs | CandyCane, Candy Cane, Candy-Cane, candycane |
| EQAoJw7BpOcBD3y9voMuEQ-qhS3K4gtM-6EePLxkzk8iSifX | SnoopDogg, Snoop Dogg, Snoop-Dogg, snoopdog, snoop |
| EQDz_VecErEBTLOTiR1tq0VS3lZuHHqhYmhZbthcrbFk7ztK | XmasStocking, Xmas Stocking, Xmas-Stocking, xmasstocking |
| EQCwEFfUbbR-22fn3VgxUpBil7bwBQqEHm7wgQYbWY9c08YJ | BDayCandle, B-Day Candle, BDay Candle, bdaycandle |
| EQBMcfMAZlMUr1W3X8kdEw3fJMUAaWH4-XcmE5R5RfFIY0E2 | DeskCalendar, Desk Calendar, Desk-Calendar, deskcalendar |
| EQCefrjhCD2_7HRIr2lmwt9ZaqeG_tdseBvADC66833kBS3y | HomemadeCake, Homemade Cake, Homemade-Cake, homemadecake |
| EQBIj0uF-qIASqv6qIvcTif2wKSdt4WQc4mcoBywNp5GntuG | InstantRamen, Instant Ramen, Instant-Ramen, instantramen |
| EQC6zjid8vJNEWqcXk10XjsdDLRKbcPZzbHusuEW6FokOWIm | LolPop, Lol Pop, Lol-Pop, lolpop, lollipop |
| EQBT9PbZBR6FGcZBSnwgo-DLpc0r7_X_8dlhG5UA6v9l9uJM | CookieHeart, Cookie Heart, Cookie-Heart, cookieheart |
| EQCBK_JBASAA5XVz1D17Pn--kQaMWm0b9wReVtsEdRO4Tgy9 | JesterHat, Jester Hat, Jester-Hat, jesterhat |
| EQBG-g6ahkAUGWpefWbx-D_9sQ8oWbvy6puuq78U2c4NUDFS | PlushPepe, Plush Pepe, Plush-Pepe, plushpepe |

Правила нормализации различаются по месту (все из кода):
- Алиасы: `lower()` и удаление `[\s_-]`, затем **точное** равенство (`gift-price-compare/index.js:29-39`).
- Giftstat: `lower()` и удаление `[\s'-]` (апостроф, пробел, дефис; подчёркивание **не** удаляется), точное совпадение со `slug` **или** `collection` (`:69-73`, `:86-88`).
- MarketApp (имя → адрес): `lower()` и удаление `[\s'-]`, совпадение равенством **или подстрокой в обе стороны** (`name.includes(q) || q.includes(name)`), берётся первое найденное (`:346-356`). Риск ложного совпадения (короткие имена, вложенные названия).
- Fragment (имя → slug): `lower()` и удаление `[\s'_-]`, равенство или подстрока в обе стороны по `data-value` и по видимому имени (`:251`, `:264-277`).
- Порядок определения адреса коллекции (`:398-406`): параметр `collection_address`, затем поиск по списку коллекций MarketApp (нужен токен), затем таблица алиасов, иначе `null`. Без адреса GetGems и MarketApp пропускаются.

В `whale-analytics` то же самое, но сначала идёт точное совпадение `slug`/`name` из Giftstat `/current/collections` (поле `blockchain_address`), потом алиасы (`whale-analytics/index.js:514-531`).

Для нас: таблица маленькая (11 коллекций) и неполная, поэтому полезнее правило нормализации плюс мастер-справочник из Giftstat `/current/collections` (там есть `collection_slug`, имя и `blockchain_address`).

### Формула спреда
`plugins/gift-price-compare/index.js:490-515`:

```js
const floors = Object.entries(comparison.marketplaces)
  .filter(([, v]) => v.floor > 0)
  .map(([mp, v]) => ({ marketplace: mp, floor: v.floor }))
  .sort((a, b) => a.floor - b.floor);
if (floors.length >= 2) {
  const cheapest = floors[0];
  const mostExpensive = floors[floors.length - 1];
  const spread = mostExpensive.floor - cheapest.floor;                 // :498
  const spreadPct = ((spread / cheapest.floor) * 100).toFixed(1);      // :499
  ...  note: +spreadPct > 5 ? "Potential … arbitrage" : "… likely not worth after fees"  // :510-512
```
- `spread = max(floor) − min(floor)`, `spread% = spread / min(floor) · 100`. Порог «интересно» > 5 %.
- Комиссии в формуле **не вычитаются**: строка про fees — только текст (`:512`).
- Баги и особенности:
  - в список «площадок» попадает псевдо-ключ `model_floor` (флор модели по всем маркетам, `:433-439`), и он сравнивается с флорами коллекций;
  - ключ `other` (Giftstat `marketplace=unknown`) тоже участвует;
  - флор GetGems всегда по коллекции, даже при заданной модели (`:458`), а флор MarketApp с моделью — по модели. То есть сравниваются несопоставимые величины;
  - у Fragment при наличии агрегированного значения берётся `min(агрегат, live)` (`:466-474`).

### Авторизация
- Giftstat: без ключа.
- MarketApp: `MARKETAPP_API_TOKEN` (или `context.config.marketapp_api_token`) в заголовке `Authorization` без префикса (`plugins/marketapp/index.js:24-47`).
- GetGems REST (`public-api/v1`): ключ в `Authorization` без префикса, источник `config.getgems_api_key`, env `GETGEMS_API_KEY` или файл `~/.teleton/getgems.key` (`plugins/getgems/index.js:49-59`, `:150-151`). Ключ выдаётся на getgems.io/public-api после TON Connect (из `plugins/getgems/README.md`). GraphQL в compare использует заголовок `X-Api-Key`, и ключ там необязателен (`gift-price-compare/index.js:174-175`).
- Fragment: анонимная cookie `stel_ssid` и `hash` со страницы.
- Секретов в репозитории нет (ни одного захардкоженного токена).

### Модель данных подарка
Нормализованная запись листинга в compare: `{name, price (TON, 2 знака), model, backdrop, symbol, itemNumber | address | url, marketplace}` (`:138-145`, `:216-222`, `:320-325`). Атрибуты берутся из `attributes[]` / `metadata.attributes[]` (`trait_type`/`value` у MarketApp, `traitType`/`value` у GetGems).

### Оценка / флор
Своей оценки нет. Флор = минимальная цена среди первых 5–10 листингов площадки или готовое поле флора (GetGems `floorPrice`, Giftstat `floor_price`). Из нескольких marketplace-строк Giftstat берётся минимальный (`:76-78`). Число сопоставимых, выбросы и фильтр по фону/символу не учитываются.

### Комиссии
- Единственная цифра в коде: «MRKT = off-chain Telegram Mini App with 8% commission». Это текст описания инструмента для LLM (`plugins/gift-price-compare/index.js:371`), в расчётах не используется. Не проверено.
- Порог спреда 5 % с подписью «likely not worth after fees» (`:510-512`). Это эвристика, не комиссия.
- GetGems офферы: API возвращает `royaltyPrice` и `feePrice` (nanoTON), плагин их только показывает (`plugins/getgems/index.js:753-754`). Значит, комиссия и роялти GetGems приходят из API, а не зашиты в коде.
- README: «Stars Broker … 5% commission». Это проприетарная функция, к маркетам отношения не имеет.
- Комиссии Portals, Tonnel, MarketApp и Fragment в коде не найдены.

### Покупка / продажа (на будущее, не MVP)
Оба плагина устроены одинаково: API маркета возвращает готовый набор сообщений, плагин подписывает их кошельком агента и отправляет. Кошелёк — W5 (`WalletContractV5R1`) из мнемоники в `~/.teleton/wallet.json`. RPC — `@orbs-network/ton-access`, fallback `https://toncenter.com/api/v2/jsonRPC`. `sendMode = PAY_GAS_SEPARATELY + IGNORE_ERRORS`, `bounce: true`. Ссылки: `plugins/getgems/index.js:213-271`, `plugins/marketapp/index.js:79-137`.

- **GetGems** (база `https://api.getgems.io/public-api/v1/`, ответы обёрнуты в `{response: …}`):
  - Покупка (`:899-972`): GET `nft/{addr}` → `sale.fullPrice` (nanoTON) и `sale.version`; затем POST `nfts/buy-fix-price/{addr}` с телом `{"version": <sale.version>}`; ответ `list[]` вида `{to, amount (nano), payload (base64 BOC), stateInit?}`; подпись и отправка.
  - Листинг (`:977-1055`): POST `nfts/put-on-sale-fix-price/{addr}` с телом `{ownerAddress, fullPrice: "<nanoTON строка>", currency: "TON"}`, далее так же.
  - Отмена продажи заявлена в README и манифесте (`getgems_cancel_sale`), **но в коде инструмента нет**.
  - Другие GET: `collections/top`, `collection/basic-info|stats|attributes|history|top-owners/{rawAddr}`, `nft/history/{addr}`, `nfts/on-sale/{addr}`, `offers/nft/{addr}`, `nfts/owner/{addr}`, `user-trading-info/{addr}`, `nfts/collection/{addr}`, `gifts/collections`, `gifts/collections/top`, `nfts/history/gifts` (types[]: mint, transfer, sold, cancelSale, putUpForSale, putUpForAuction, cancelAuction, burn), `nfts/offchain/on-sale/gifts?limit&after`. Последний — off-chain (неминтованные) подарки, выставленные на GetGems; поля `sale.fullPrice`/`minBid` в nanoTON (`:1497-1557`).
  - Лимиты в клиенте (`:66-68`, `:102-128`, `:153-159`): минимум 800 мс между запросами, не более 350 запросов за 5 мин; на 429 ретрай (до 3 раз) с ожиданием `retry-after` (≤ 30 с) плюс jitter до 1 с; GET-кэш 60 с, для справочников 120 с.
- **MarketApp** (база `https://api.marketapp.ws/v1`, все POST с JSON, `Authorization: <token>`):
  - Покупка: POST `nfts/buy/` с телом `{"data":[{"nft_address","price": <TON числом>,"currency":"TON"}]}` (`:405-421`).
  - Листинг: POST `nfts/sale/` с телом `{"owner_address","data":[{nft_address, price (TON), currency:"TON"}]}` (`:477-490`).
  - Смена цены: POST `nfts/change_price/`, тело как у листинга (`:544-557`).
  - Снятие: POST `nfts/cancel_sale/` с телом `{"owner_address","nft_addresses":[…]}` (`:601-608`).
  - Ответ: `transaction.messages[]` вида `{address, amount (nano), payload (b64 BOC), stateInit?}`.
  - GET: `collections/gifts/` (`extra_data.floor/volume7d/volume30d/rent_floor` в nanoTON, `owners`, `on_sale_all`, `on_sale_onchain`), `gifts/onsale/` (`collection_address, model, symbol, backdrop, min_price, max_price, sort_by ∈ {min_bid_asc, min_bid_desc, recently_touch}, cursor`; до 100 на страницу), `gifts/history/` (`collection_address, limit ≤ 100, cursor`; поля `nft_address, event_type, details.{src,dst,price_nano,currency,market_name}`), `nfts/{addr}/`, `collections/{addr}/attributes/` (`attributes[].values[].{value,count,floor}`).
  - Единицы `min_price`/`max_price` в фильтре по описанию «in TON»; что ждёт сервер, в коде не проверяется.

### Предохранители и лимиты
- Торговля: проверяются только `price > 0` и непустой список сообщений. Нет:
  - проверки адресатов и сумм в транзакции, которую вернул сервер (слепая подпись);
  - лимита бюджета, подтверждения и dry-run;
  - ожидания подтверждения on-chain («Allow ~30 seconds»).

  Флаг `IGNORE_ERRORS` скрывает ошибки отправки. Для нас это антипример.
- У Giftstat, MarketApp и Fragment троттлинга и ретраев нет, есть только таймауты (12–15 с, 20 с у POST MarketApp).

### Уведомления / UI
Нет. Это инструменты LLM-агента: ответы — JSON, плюс картинки-графики через QuickChart в плагине `chart`.

### Хранение состояния
SQLite через `sdk.db` из Teleton (таблица `whale_snapshots`, плюс таблицы `invoices`). Кэш GetGems и состояние health-check держатся в памяти.

## Что берём
| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Правило нормализации имён коллекций (lower + удалить пробелы/`_`/`-`/апостроф, точное равенство) и 11 алиасов как стартовый seed | `pricing/aliases.py` | переписать. Подстрочное сопоставление в обе стороны НЕ берём (ложные совпадения). Мастер-справочник строить из Giftstat `/current/collections` (`collection_slug` + имя + `blockchain_address`) |
| Формула спреда `(max−min)/min·100` | `pricing/` (арбитраж) | идея; у нас считать по **net** после комиссий и только по сопоставимым величинам (одинаковый уровень: коллекция/модель/фон) |
| Giftstat как резервный и сверочный источник флоров коллекции и модели, история и индекс | `pricing/` (fallback) | формат API; с throttle и таймаутом, единицы проверить на живом ответе |
| Эвристика стратегий кошелька (пороги 3×, 2×, 0.3) и z-score детектор аномалий / wash-trading | аналитика (позже) | идея |
| Паттерн клиента GetGems: 800 мс интервал, 350/5 мин, 429 + retry-after + jitter, кэш 60–120 с | `markets/*` | идея |
| Схема покупки/листинга GetGems и MarketApp («сервер отдаёт сообщения → подпись W5») | (не MVP) | только описание, с обязательной проверкой сообщений перед подписью |

## Что НЕ берём и почему
- Код целиком (AGENTS.md §4.3); торговые функции со слепой подписью и `IGNORE_ERRORS`.
- Fragment-скрейпинг HTML regex-ами: хрупкий, к нашим маркетам не относится.
- Классификацию «китов» как «держателей»: на деле это топ покупателей по выборке продаж, балансы не проверяются.
- Сравнение флоров «коллекция против модели» и смешивание агрегированных и live-флоров.

## Открытые вопросы
1. Точные схемы ответов Giftstat (единицы `floor_price`, наличие `mrkt` при `marketplace=all`, поля v2 `/history/collections/floor`) в коде угадываются fallback-ами. Нужна проверка на живом ответе.
2. Лимиты запросов Giftstat в коде не найдены.
3. Метки «Diamond Hands / Flipper / Accumulator» есть только в README, в коде их нет. Реальные метки: `accumulating / distributing / trading / mixed / insufficient_data`.
4. `getgems_cancel_sale` заявлен в README и манифесте, но в коде не реализован.
5. Комиссии всех площадок в коде не найдены (кроме текстового «MRKT 8%»).

## Для MARKETS.md
- **Giftstat (агрегатор, не маркет)**: без авторизации, GET, JSON с ответом в `data[]` (из кода `plugins/giftstat/index.js:21-38`).
  - v1 `https://api.giftstat.app`:
    - `/current/collections?fields&limit&offset` → `blockchain_address`, `collection_slug`, `collection`, `total_amount` (из кода `whale-analytics/index.js:148-155`);
    - `/current/collections/floor?marketplace=portals|tonnel|fragment|getgems|all&limit&offset` → `slug`, `collection`, `marketplace`, `floor_price` (TON по коду, без конвертации) (из кода `gift-price-compare/index.js:60,70-79`);
    - `/current/collections/models/floor?limit&offset` → `collection_slug`, `model`, `floor_price` (из кода `:61,87-92`);
    - `/current/collections/models`, `/models/stat`, `/backdrops`, `/symbols`, `/current/thematics`, `/current/thematics/lines`, `/current/ton-rate` (из кода, поля не разбираются);
    - `/history/collections/floor?marketplace=portals|tonnel|getgems&scale=day|hour&days&limit&offset` (из кода `giftstat/index.js:321-327`).
  - v2 `https://apiv2.giftstat.app`:
    - `/history/index/floor` (поля по подсказке: `price`, `upper_threshhold`, `lower_threshhold`, `dt`; ~30 мин);
    - `/history/collections/floor?limit&offset` (по подсказке: `floor_price`, `portals_floor_price`, `tonnel_floor_price`, `mrkt_floor_price`) (из кода, поля не проверены).
  - Документация: wiki.giftstat.app (из README плагина).
- **MarketApp (on-chain, marketapp.ws; не путать с MRKT)**: база `https://api.marketapp.ws/v1`, заголовок `Authorization: <token>` без `Bearer` (из кода `plugins/marketapp/index.js:20,41-47`). Цены в ответах в nanoTON (`min_bid`, `status.<type>.price_nano`, `extra_data.floor`), в теле buy/sale цена в TON числом плюс `currency:"TON"`. Пагинация `cursor`, `limit ≤ 100`. Эндпоинты:
  - GET `collections/gifts/`;
  - GET `gifts/onsale/?collection_address&model&symbol&backdrop&min_price&max_price&sort_by=min_bid_asc|min_bid_desc|recently_touch&cursor`;
  - GET `gifts/history/?collection_address&limit&cursor`;
  - GET `nfts/{addr}/`;
  - GET `collections/{addr}/attributes/`;
  - POST `nfts/buy/` `{data:[{nft_address,price,currency}]}`;
  - POST `nfts/sale/` `{owner_address,data:[…]}`;
  - POST `nfts/change_price/`;
  - POST `nfts/cancel_sale/` `{owner_address,nft_addresses:[]}`.

  POST возвращает `transaction.messages[{address,amount,payload,stateInit}]` для подписи кошельком (из кода `:387-629`).
- **GetGems REST**: база `https://api.getgems.io/public-api/v1/`, заголовок `Authorization: <key>` без префикса, ответ обёрнут в `{response:…}`, цены в nanoTON (из кода `plugins/getgems/index.js:33,132-169`).
  - Покупка: GET `nft/{addr}` (`sale.fullPrice`, `sale.version`), затем POST `nfts/buy-fix-price/{addr}` `{version}`.
  - Листинг: POST `nfts/put-on-sale-fix-price/{addr}` `{ownerAddress, fullPrice: "<nano>", currency}`.
  - Ответ: `list[{to,amount,payload,stateInit}]` (из кода `:899-1055`).
  - История подарков: GET `nfts/history/gifts?limit&after&types[]=sold…` → `items[].{collectionAddress,address,name,time,typeData.{priceNano,newOwner,oldOwner}}`, `cursor` (из кода `whale-analytics/index.js:107-139`).
  - Off-chain подарки на продаже: GET `nfts/offchain/on-sale/gifts?limit≤100&after` (из кода `getgems/index.js:1522`).
  - Клиентские лимиты автора: ≥ 800 мс между запросами, ≤ 350 за 5 мин, 429 → retry-after (из кода `:102-128`). Официальные лимиты не установлены.
- **GetGems GraphQL**: POST `https://api.getgems.io/graphql`, `X-Api-Key` опционально, `nftCollectionByAddress(address){floorPrice nftItems(first, filter:{saleType:ON_SALE, attributes:[{traitType,value}]}, sort:PRICE_ASC){items{name address sale{fullPrice} attributes{traitType value}}}}`, цены в nanoTON (из кода `gift-price-compare/index.js:169-229`).
- **Fragment** (скрейпинг): GET `/` → cookie `stel_ssid` и `hash`; GET `/gifts` с `X-Requested-With: XMLHttpRequest` → JSON `h` (HTML коллекций); POST `/api?hash=…` form `method=searchAuctions&type=gifts&sort=price_asc&filter=sale&view=list&collection=<slug>` → `{ok, html}`, цены строкой в TON (из кода `gift-price-compare/index.js:231-344`).
- **Portals / Tonnel / MRKT**: в этом репо прямых эндпоинтов нет, только флоры через Giftstat (из кода).
- **Комиссии**: «MRKT 8%» — только текст описания инструмента, не проверено (из кода `gift-price-compare/index.js:371`). GetGems отдаёт `royaltyPrice`/`feePrice` в офферах (из кода `getgems/index.js:753-754`). Других цифр в коде не найдено.
