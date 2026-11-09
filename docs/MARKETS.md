# Рынки: сводка API (Portals, MRKT, Tonnel)

Обновлено: 2026-11-09, после чтения исходников (Этап 0, второй проход). Подробности и номера строк — в отчётах `docs/research/`.

**Ни один пункт не проверен живым запросом.** Пометки источника:

- **[код: X]** — прочитано в исходниках репозитория X (коммит в отчёте).
- **[README: X]** — только из README/документации X.
- **[фикстура: X]** — из тестовых фикстур X (данные автора, не наши).
- **[подозр.: X]** — из README подозрительного репозитория (раздел I), только как подсказка.
- **[?]** — не установлено. **[✗]** — источники расходятся.
- «проверено на живом ответе» — будет ставиться на Этапе 2 после записи фикстур.

Свежесть источников: topcvetok — 2026-11-01 (самый свежий, но только чтение); aportalsmp — 2025-11-30; amrkt — 2026-03-22; boostNT — 2026-02/03; portalsmp — 2025-08 (домен устарел); tonnelmp — код 2025-06-17 (**может быть устаревшим, проверять каждый путь на Этапе 2, решение владельца 2026-11-09**).

---

## 1. Portals

| Параметр | Значение |
|---|---|
| Base URL | `https://portal-market.com/api/` [код: aportalsmp, topcvetok; README: boostNT]. `portals-market.com` — старый домен [код: portalsmp] [✗ разрешено: домен сменился 2025-11-06]. Ранее `market.portals.tg` |
| Заголовки | `Origin: https://portal-market.com`, `Referer: https://portal-market.com/`, `Accept: application/json, text/plain, */*`, UA Chrome/Edge 137 [код: aportalsmp]. TLS `curl_cffi impersonate` (`chrome110` [код: aportalsmp], `chrome` [код: topcvetok]); topcvetok — HTTP/1.1, `accept-encoding: identity` |
| Авторизация | `Authorization: tma <initData>` [код: portalsmp, aportalsmp]. initData: `messages.requestAppWebView(peer=@portals, app=InputBotAppShortName(short_name="market"), platform="desktop")` → из `url` подстрока между `tgWebAppData=` и `&tgWebAppVersion`, один `unquote` [код: aportalsmp auth.py:30-44]. boostNT — `platform="android"` [README] |
| Без авторизации | `GET nfts/search`, `GET collections`, `GET nfts/{id}` работают без токена [код + фикстура: topcvetok]. `collections/filters`, `collections/floors` — публичные [подозр.: OnyxTarantulaLoop] |
| Срок токена | [?] Оценки авторов: «более суток» / «1–7 суток». Стратегия: перевыпуск по 401 (D-005) |
| Поиск | `GET nfts/search?offset&limit&sort_by=<поле>+<asc\|desc>&status=listed&collection_ids=<uuid,…>&filter_by_models&filter_by_backdrops&filter_by_symbols&min_price&max_price&exclude_bundled=true&premarket_status=all` → `{results:[gift]}` [код: aportalsmp gifts.py:160-228]. Старый вариант — `filter_by_collections=<имена Title Case>` [код: portalsmp; topcvetok поддерживает оба]. Сортировки: `price`, `listed_at` (desc), `external_collection_number`, `model_rarity` [код: portalsmp] |
| Объект подарка | `id (uuid), tg_id, external_collection_number, collection_id, name, photo_url, price ("строка TON"), floor_price, attributes[{type: model\|symbol\|backdrop, value, rarity_per_mille}], listed_at, status, animation_url, emoji_id, unlocks_at` [код: aportalsmp Objects.py; фикстура: topcvetok] |
| Коллекции | `GET collections?limit=&search=` → `{collections:[{id, name, short_name, floor_price, day_volume, volume, supply, photo_url, sales_24h_count}]}` [код: aportalsmp; topcvetok] |
| Флоры | `GET collections/floors` → `{floorPrices:{short_name: price}}`; `GET collections/filters?short_names=<sn>` → `{floor_prices:{sn:{models, backdrops, symbols}}}` [код: portalsmp, aportalsmp] |
| Карточка | `GET nfts/{id}` → объект с `status` (`listed`/`sold`), `price` [код: topcvetok] |
| Активность рынка | `GET market/actions/?offset&limit&sort_by&action_types=buy,listing,price_update,offer&filter_by_collections=…` → `{actions:[{nft, type, amount, offer_id, created_at}]}` [код: portalsmp, aportalsmp]. Источник продаж для медианы 24 ч (topcvetok его не использует, берёт только `sales_24h_count`) |
| Мои | `GET users/actions/`, `GET nfts/owned?status=listed\|unlisted` → `{nfts}`; points: `points/me` [aportalsmp] / `points/my-points` [portalsmp] |
| Покупка | `POST nfts` `{"nft_details":[{"id":"<uuid>","price":"<TON строкой>"}]}` → `{total_requested, total_purchased, total_failed, total_spent, purchase_results:[{id, status, reason, price, error_message}]}` [код: aportalsmp gifts.py:525-580]. **Успех — по `total_purchased`/`status`, не по HTTP-коду.** Цена передаётся, проверяет ли её сервер — [?]. Ранее было поле `owner_id` (убрано) |
| Листинг | `POST nfts/bulk-list` `{"nft_prices":[{"nft_id","price":"<str>"}]}` → `{successful_nfts, failed_nfts}`; смена цены `POST nfts/{id}/list` `{"price":"<str>"}` [код: portalsmp, aportalsmp] |
| Офферы | `POST offers` `{"offer":{nft_id, offer_price, expiration_days?}}`, `PATCH offers/{id}` `{amount}`, `POST offers/{id}/cancel`, `GET offers/placed\|received`; коллекционные `POST collection-offers/`, `.../cancel`, `GET collection-offers/{uuid}/top\|all` [код: portalsmp, aportalsmp]. Не MVP |
| Баланс | `GET users/wallets/` → `{balance, frozen_funds}` [код: aportalsmp account.py] |
| Вывод | `POST users/wallets/withdraw` `{"amount":"<str>","external_address"}` → `{id}` [код]. Агент не вызывает (AGENTS.md §4.6) |
| Пагинация | `offset` + `limit`; max `limit`: 100 [README: boostNT] / «вероятно 20» [код-комментарий: portalsmp] / topcvetok использует ≤20 [✗] |
| Лимиты | В коде обёрток обработки 429 нет. topcvetok: ≥1,2 с между запросами, опрос 5 с, 429 → `retry-after` [код]. Заголовок `x-ratelimit-limit: 2` на search и 12 на floors, 429 уже на 2 rps [подозр.: OnyxTarantulaLoop] |
| Цены | TON, **десятичная строка** (`"1.85"`, `"44"`), не nano [код: все три]. Парсить через Decimal → nanoTON (D-012) |
| Ссылка на лот | `https://t.me/portals/market?startapp=gift_<id>` [код: topcvetok] |

## 2. MRKT

| Параметр | Значение |
|---|---|
| Base URL | `https://api.tgmrkt.io/api/v1` [код: amrkt; README: boostNT; код: topcvetok до b0e81f2] |
| Заголовки | `Authorization: <token>` (без Bearer) + `Cookie: access_token=<token>`; `Origin: https://cdn.tgmrkt.io`, `Referer: https://cdn.tgmrkt.io/`, `Sec-Fetch-Site: same-site`, `Sec-Fetch-Mode: cors` [код: amrkt]. `Referer` добавлен boostNT как «fix 429» [README: boostNT, 2026-03-30]. TLS `impersonate="chrome124"` [код: amrkt] |
| Авторизация | `POST /auth` `{"data":"<initData>"}` → `{"token"}` [код: amrkt; README: boostNT]. initData: `requestAppWebView(peer=@mrkt, short_name="app", platform="android")`, та же вырезка `tgWebAppData` + `unquote` [код: amrkt] |
| Срок токена | [?] («более суток», boostNT). amrkt: перевыпуск по 401 + 1 повтор. Ответ на протухший токен (401 или 404) — [?] |
| Поиск | `POST /gifts/saling` `{collectionNames[], modelNames[], backdropNames[], symbolNames[], ordering:"Price"\|"ModelRarity"\|"BackgroundRarity"\|"SymbolRarity"\|null, lowToHigh, minPrice, maxPrice (nanoTON), mintable, number, count, cursor:"", query, promotedFirst}` → `{gifts[], total, cursor}` [код: amrkt; README: boostNT]. topcvetok слал ещё `isPremarket, isNew, luckyBuy, craftable, removeSelfSales, isTransferable, …` [код: topcvetok b0e81f2^] |
| Пагинация | курсорная, `cursor:""` — первая, `null` — конец. `count` ≤ 20 [README: boostNT; topcvetok] vs 50 в примере amrkt [✗] |
| Объект подарка | ~60 полей; ключевые: `id, number, collectionName, modelName, backdropName, symbolName, salePrice, salePriceWithoutFee, isOnSale, isOnAuction, isLocked, isLockedForSale, premarketStatus, nextResaleDate, floorPriceNanoTONsByCollection, floorPriceNanoTONsByBackdropModel` [код: amrkt models.py; фикстура: topcvetok]. Полная таблица — `thebrainair__amrkt.md` |
| Коллекции | `GET /gifts/collections` → `[{name, title, floorPriceNanoTons, previousDayFloorPriceNanoTons, volume, cashbackCoef, isHidden}]` [код: amrkt] |
| Карточка | `GET /gifts/gift/{id}` [код: amrkt] |
| Лента (продажи) | `POST /feed`: у amrkt тело `{}` → `{items:[{type: listing\|sale\|change_price, id, gift, amount, date}]}`; у topcvetok `{count≤20, cursor, type:["Sale","Listing","ChangePrice"], ordering:"Latest", …}` [код]. Отдельного history — не найдено. Источник медианы продаж 24 ч |
| Покупка | `POST /gifts/buy` `{"Ids":[id]}` (заглавная I) → `[{userGift, price}]` [код: amrkt]. **Цена не передаётся** — риск покупки по изменённой цене; перед вызовом обязательна повторная проверка `salePrice` (Этап 7) |
| Листинг | `POST /gifts/sale` `{"ids","prices"(nanoTON)}`; `POST /gifts/sale/cancel` `{"ids"}`; `POST /gifts/sale/change-price` `{"ids","prices"}` [код: amrkt] |
| Инвентарь / возврат | `POST /gifts` (тело как у saling); `POST /gifts/return` `{"Ids"}` [код: amrkt] |
| Баланс | `GET /balance` → `{soft, hard, totalHard, hardLocked, stars, starsFotWithdraw, …}` в nanoTON [код: amrkt]. Что такое soft vs hard и какой списывается при покупке — **в коде не найдено** [?]; косвенно hard — основной (README amrkt печатает его как «Balance») |
| Прочее | `GET /me` (`serverTime`), `GET /transactions/await`, `POST /offers/create {price, giftSaleId}`, `POST /offers/cancel?offerId=`, `GET /activities` [код: amrkt] |
| Лимиты | в обёртках нет обработки 429. topcvetok: ≥1,05 с между запросами (для Swift). [?] |
| Цены | **nanoTON (int)** везде, включая `minPrice/maxPrice` [код: amrkt]. `salePriceWithoutFee = salePrice / 1.02` в фикстуре → вероятно 2% надбавка покупателя [фикстура: topcvetok; не подтверждено] |
| Ссылка | `https://t.me/mrkt/app?startapp=gift<id без '-'>` [код: topcvetok] |
| Альтернатива | topcvetok с 2026-10-29 берёт MRKT через партнёрский API Swift Gifts (`partners.swiftgifts.tg`, `x-api-key`, платный ключ) [код: topcvetok]. Мы — напрямую (D-005); Swift не используем без отдельного решения |

## 3. Tonnel

Код tonnelmp не менялся с 2025-06-17. Хосты чтения подтверждаются свежим topcvetok (2026-11); пути покупки/листинга — только tonnelmp и README раздела I.

| Параметр | Значение |
|---|---|
| Хосты | Чтение: `https://gifts2.tonnel.network/api/` (+ `gifts3.tonnel.network/api/filterStats`). Деньги (buy/list/cancel/withdraw): `https://gifts.coffin.meme/api/` [код: tonnelmp]. События: `gifts.coffin.meme` [код: topcvetok] |
| Заголовки | `Origin: https://market.tonnel.network`, `Referer: https://market.tonnel.network/`, `content-type: application/json`, `sec-fetch-*`, UA; без cookies. `curl_cffi impersonate` (`chrome110` [код: tonnelmp], `chrome` [код: topcvetok]). Без имитации — 403 (Cloudflare) [README + код] |
| Авторизация | Сырой initData (`web-initData` из localStorage Mini App) **в теле**: `user_auth` в `pageGifts` (пустая строка = анонимно), `authData` в остальных [код: tonnelmp]. Программного получения initData в коде нет [?] — делаем через Telethon `requestAppWebView` (бот/short_name уточнить на Этапе 2) |
| Поиск | `POST gifts2…/api/pageGifts` `{page≥1, limit≤30, sort:"<JSON-строка>", filter:"<JSON-строка>", price_range:[min,max]\|0\|null, ref:0, user_auth}` → JSON-массив [код: tonnelmp, topcvetok]. Фильтр активных: `{"price":{"$exists":true},"buyer":{"$exists":false},"refunded":{"$ne":true},"export_at":{"$exists":true},"asset":"TON"}` + `gift_name`, `model`, `backdrop`, `symbol` (не `pattern`, как в boostNT [✗]) |
| Объект подарка | `gift_id` (внутр.), `gift_num`, `name`, `model`/`backdrop`/`symbol` как `"Name (r%)"`, `price` (TON, число), `asset`, `status` (`forsale`), `auction`, `dutchAuctionData`, `premarketData`, `underLoan`, `export_at` [код + фикстура: topcvetok; код: tonnelmp]. Бандлы: `gift_id < 0` |
| События (WebSocket) | `wss://gifts.coffin.meme/api/marketplace/ws`, без подписки, кадры JSON. Типы: `listing.created` (`data.sale_type` FIXED/DUTCH), `listing.price_changed` (`previous_price`), `sale.completed`, `premarket.listing_created`. Догонка: `GET https://gifts.coffin.meme/api/marketplace/events?after=<eventId>&limit=100` → `{events, nextAfter}` [код + фикстура: topcvetok]. Кто стоит за `coffin.meme` — [?]; tonnelmp шлёт туда же покупки, т.е. это бэкенд Tonnel |
| Флоры | `POST …/api/filterStats` `{authData}` → `{status, data:{"Gift_Model (r%)":{floorPrice, howMany}}}`, флор без 10% [код: tonnelmp]. Требует initData [подозр.: Onyx] |
| История продаж | `POST gifts2…/api/saleHistory` `{authData, page, limit≤50, type: ALL\|SALE\|INTERNAL_SALE\|BID, filter:{}, sort:{}}` (объекты, не строки) [код: tonnelmp]. Плюс `sale.completed` из WS |
| Баланс | `POST gifts2…/api/balance/info` `{authData}` → `{balance, usdtBalance, tonnelBalance, memo, transferGift, …}` [код: tonnelmp] |
| Покупка | `POST gifts.coffin.meme/api/buyGift/{gift_id}` `{authData, asset:"TON", price:<TON цена листинга без 10%>, timestamp:"<unix>", wtf:"<токен>"}` [код: tonnelmp]. Списывается `price × 1.1` [README: tonnelmp; подозр.: раздел I]. Ответ `{"status":"success"\|"error"}` [подозр.: Onyx] |
| Листинг | `POST …/api/listForSale` `{authData, gift_id, price, asset, timestamp, wtf}`; `POST …/api/cancelSale` `{authData, gift_id, timestamp, wtf}`; `changePrice` — нет; `POST …/api/unlock` `{authData, sale_id}` (0.1 TON, README); `returnGift`; `balance/withdraw` [код: tonnelmp] |
| Токен `wtf` | CryptoJS-совместимый AES-256-CBC над строкой unix-времени; ключ/IV — EVP_BytesToKey(MD5) от парольной фразы фронтенда Tonnel + соль; base64(`Salted__`+salt+ct). Только для buy/list/cancel [код: tonnelmp wtf.py]. Парольную фразу брать из актуального фронтенда, хранить в конфиге/секретах, не в коде |
| Пагинация | `page` + `limit` ≤ 30 |
| Лимиты | topcvetok: до 3 попыток (2 с, 4 с), 403/5xx → повтор, 429 → `retry-after` (по умолчанию 300 с), 1,2 с между коллекциями [код]. Официальные — [?] |
| Цены | **TON, число (float в JSON)**, не nano [код: tonnelmp, topcvetok]. Парсить через `Decimal(str(x))` → nanoTON |
| Ссылка | `https://t.me/tonnel_network_bot/gift?startapp=<gift_id>` [код: topcvetok] |

## 4. Telegram (MTProto)

- `payments.getUniqueStarGiftValueInfo(slug)` — вспомогательный сигнал оценки (D-010), подробности `docs/research/SUMMARY.md` §3. Суммы в фиате аккаунта.
- `payments.getStarGifts(hash)` — магазин подарков (не MVP): при `StarGiftsNotModified` ничего не делать; опрос 10–15 с [код: gifts-tracker, telegram-gifts-radar].
- Ссылки на подарок: `https://t.me/nft/<Slug>-<n>`; картинка `https://nft.fragment.com/gift/<slug>-<n>.small.jpg` [код: topcvetok].

## 5. Вспомогательные внешние источники (резерв, не зависимость, D-011)

| Источник | Что даёт | Авторизация | Статус |
|---|---|---|---|
| Giftstat `https://api.giftstat.app` | `/current/collections/floor?marketplace=portals\|tonnel\|…\|all`, `/current/collections/models/floor`, история флоров; v2 `apiv2.giftstat.app/history/collections/floor` (поля `portals_floor_price`, `tonnel_floor_price`, `mrkt_floor_price` — по подсказке, не проверено) | нет | [код: morgan-gift-plugins]; лимиты [?] |
| Clue `https://app.clue.tg/api/mono/resolve?url=<slug-n>` | `{"score":0..100}` — монохромность, порог 80 у topcvetok | нет | [код: topcvetok]; лимиты [?] |
| CoinGecko `simple/price?ids=the-open-network&vs_currencies=…` | курс TON | нет | [код: topcvetok] |

## 6. Комиссии (D-009: всё `verified=false`)

| Маркет | Покупка | Продажа | Вывод | Источники |
|---|---|---|---|---|
| Portals | 0% [подозр.: раздел I; пост канала] | 5% [подозр.: раздел I] / 2.5% (vc.ru) [✗] | 0.1 TON [подозр.: раздел I] | в коде обёрток комиссий нет; topcvetok резервирует 2% на перепродажу (не тариф) |
| Tonnel | +10% к цене листинга [README: tonnelmp; подозр.: раздел I] | 0% [подозр.: раздел I] / 3–4% (dev.to) [✗] | 0.001 TON, мин. 0.5 [докстринг tonnelmp]; 0 [подозр.] [✗]. Разблокировка листинга 0.1 TON [README: tonnelmp] | topcvetok резерв 2% |
| MRKT | ≈2% (из `salePriceWithoutFee = salePrice/1.02`) [фикстура: topcvetok] | 5% [подозр.: раздел I] / 2% / «8%» [текст morgan] [✗] | [?] | topcvetok резерв 1,96% |
| Telegram ресейл | — | 20% [подозр.: раздел I] | — | — |

Проверка — задача владельца на минимальных суммах (условие Этапа 7).

## 7. Временный бюджет запросов (D-008, решение проекта)

Не чаще 1 запроса списка листингов на маркет раз в 5 с, ≤ 1 запрос/с суммарно на маркет, backoff с jitter на 429/5xx с учётом `retry-after`, таймаут 10 с. Для Portals дополнительно ≥ 1,2 с между запросами (опыт topcvetok). WebSocket Tonnel — одно соединение, не считается в бюджет запросов.

## 8. Реализация (Этап 2)

Клиенты: `backend/app/markets/{portals,mrkt,tonnel}.py`; разрешённые пути — `READ_ROUTES` в каждом файле (D-017). Фикстуры «из кода» — `backend/tests/fixtures/code/` (поле `_source`). Живые ответы будут в `backend/tests/fixtures/live/` после шага 2.8.

## 9. Что ещё не установлено (проверить на Этапе 2 живыми запросами на чтение)

- Актуальность путей tonnelmp (2025-06) — каждый путь чтения отметить «проверено» или «устарело».
- Бот и `short_name` Mini App Tonnel для получения initData через Telethon.
- Срок жизни токенов всех трёх маркетов; ответ MRKT на протухший токен.
- Максимум `limit`/`count` (Portals 20/100, MRKT 20/50).
- Схема ответа `pageGifts` и `saling` на текущий момент (поля могли добавиться).
- soft/hard баланс MRKT (только чтение `GET /balance`, без трат).
- Официальные лимиты частоты; заголовки `x-ratelimit-*` Portals.
- Владелец `gifts.coffin.meme` (косвенно — бэкенд Tonnel).

Не проверяется агентом вообще (только описание): покупка, листинг, вывод — до разрешения Этапа 7.
