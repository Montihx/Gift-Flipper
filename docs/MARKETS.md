# Рынки: сводка API (Portals, MRKT, Tonnel)

Обновлено: 2026-11-09. Источники — чужие README (не код) и страницы PyPI, см. `docs/research/`. **Ничего из этого не проверено запросами к самим маркетам** (проект запрещает это на Этапе 0), поэтому статус везде: «из README» / «заявлено» / «не установлено». Поля «проверено» нет ни у одного пункта.

Обозначения: **[R]** — из README/страницы PyPI (пересказ, сверить с живым ответом); **[?]** — не установлено; **[✗]** — расхождение между источниками.

## 1. Portals

| Параметр | Значение |
|---|---|
| URL | Web-приложение: `portal-market.com` / `portals-market.com` [✗: в README boostNT `portal-market.com`, в README portalsmp `portals-market.com` — проверить, какой верный]. API (boostNT): `https://portal-market.com/api` [R] |
| Бот / Mini App | бот `portals`, `short_name='market'` (получение `initData` через `RequestAppWebView`, platform `android`) [R, boostNT] |
| Авторизация | заголовок `Authorization: tma <initData>` [R]. Токен берут из DevTools или через сессию Telegram (`update_auth()` в portalsmp, Pyrogram/kurigram) |
| Срок токена | не установлен. Оценки авторов: «точно более суток» (boostNT), «примерно 1–7 суток» (portalsmp). Стратегия: перевыпуск по 401 |
| Поиск | `GET /api/nfts/search` [R]. Параметры: `collection_ids` (через запятую), `filter_by_models`, `filter_by_backdrops`, `external_collection_number`, `exclude_bundled`, `premarket_status` (`all`/`only_premarket`/`without_premarket`), `min_price`, `max_price`, `status` (`listed`/`unlisted`), `sort_by` (`price`, `listed_at` (только desc), `external_collection_number`, `model_rarity`; формат `поле desc`/`поле asc`), `limit`, `offset`. Ответ: ключ `results`; схема объекта не описана [?] |
| Коллекции | `GET /api/collections?search=<имя>&limit=10`, ключ ответа `collections`, ID в `collections[0].id` [R] |
| Флоры | функции `giftsFloors()`, `filterFloors()` в portalsmp [R: только имена]; пути, формат ответа [?] |
| Продажи / активность | `marketActivity()`, `myActivity()` в portalsmp [R: только имена]; пути [?] |
| Покупка | `buy(nft_id, owner_id, price, authData)` в portalsmp [R: сигнатура; в changelog `owner_id` убран, в README остался — расхождение]; путь, тело, единицы цены [?] |
| Листинг | `sale(nft_id, price, authData)`, `bulkList()` (автор: «Not tested yet»), `changePrice()` [R: имена/сигнатуры]; пути [?] |
| Офферы | `makeOffer`, `cancelOffer`, `editOffer`, `topOffer`, коллекционные офферы [R: только имена]; `expiration_days` 0 или 7 |
| Баланс | `myBalances()`, `myPoints()` [R: имена] |
| Вывод | `withdrawPortals()`; предупреждение README: адреса `UQ` могут работать только как `EQ` [R] |
| Пагинация | `offset` + `limit`; `limit` ≤ 100 (boostNT). В portalsmp `offset` = номер страницы × `limit`. Признака последней страницы и общего счётчика в README нет [?] |
| Лимиты запросов | не установлены [?]. Работающий бюджет для Этапа 2 см. §6 |
| Формат цен | в примере portalsmp цены строкой (`"price": "44"`, `"floor_price": "31.43"`), единица не названа; в параметрах `int\|float` [?] |
| Комиссии | см. §5, не проверено |
| Защита от ботов | в прочитанном README не описана [?] |

## 2. MRKT

| Параметр | Значение |
|---|---|
| URL | API: `https://api.tgmrkt.io/api/v1/` [R, boostNT + пакет `mrkts`]. Referer в примере: `https://cdn.tgmrkt.io/` |
| Авторизация | `POST /api/v1/auth` с телом `{"data": "<initData>"}` → в ответе `token`; далее заголовок `Authorization` [R, boostNT]. amrkt получает токен через сессию Telegram и обновляет сам |
| Срок токена | не установлен («точно более суток», boostNT) |
| Поиск (листинги) | `POST /api/v1/gifts/saling` [R]. Тело: `collectionNames`, `modelNames`, `backdropNames`, `symbolNames` (списки), `ordering` (`Price`/`ModelRarity`/`BackgroundRarity`/`SymbolRarity`/`None`), `lowToHigh`, `minPrice`, `maxPrice`, `mintable`, `number`, `count`, `cursor`, `query`, `promotedFirst` (два последних — назначение неизвестно). Ответ: `gifts`, `cursor` |
| Каталог | у пакета `mrkts`: `gifts.collections`, `models`, `backdrops` (имена методов) [R: пути неизвестны] |
| История продаж / лента | `gifts.history`, `gifts.feed` (имена методов `mrkts`); `/api/v1/feed` из задания A не подтверждён [R: пути, тела неизвестны] |
| Покупка | `buy_gifts(gift_ids)` (amrkt), `gifts.buy` (mrkts) [R: только имена]; путь, тело [?] |
| Листинг | `sell_gifts(gift_ids, prices)`, цены в **nanoTON** (amrkt); `gifts.sale` (mrkts) [R] |
| Инвентарь / возврат | `get_inventory`, `return_gifts` (в Telegram) [R: имена] |
| Баланс | `get_balance()` → `soft`, `hard`, `stars` [R]. Какой баланс тратится при покупке — [?] |
| Офферы | `market.offers.activities` (mrkts) [R: имя]; детали [?] |
| Пагинация | курсорная: `cursor` пустая строка → первая страница; следующий — из ответа; `None`/пусто или `<count` — конец [R] |
| Лимиты | `count` ≤ 20 (boostNT) [✗: пример amrkt использует `count=50`]; частота запросов не установлена [?] |
| Формат цен | в запросах `minPrice/maxPrice` единицы не описаны [?]; листинг — nanoTON (amrkt) |
| Комиссии | см. §5, не проверено |
| Защита от ботов | amrkt по умолчанию: браузерные заголовки, Cookie, имитация TLS (`impersonate`, по умолчанию `chrome124`), случайный User-Agent; прокси поддерживаются [R]. Нужность этого для самого маркета не проверена |

## 3. Tonnel

| Параметр | Значение |
|---|---|
| URL | Mini App: `market.tonnel.network`; API: `https://gifts2.tonnel.network/api/…` [R, boostNT] |
| Авторизация | `authData` = значение `web-initData` из Local Storage сайта (сырой `initData`) [R, tonnelmp]. В теле запросов поиска поле `user_auth` (пустая строка = без входа) [R, boostNT]. Для `getGifts`/`getAuctions` вход не нужен [R]. Формат/подпись для покупки [?] |
| Срок токена | не установлен [?] |
| Поиск | `POST /api/pageGifts` [R]. Тело JSON: `page`, `limit` (≤ 30), `sort` (**строка с JSON**, напр. `{"message_post_time":-1,"gift_id":-1}`), `filter` (**строка с JSON**), `price_range` (`[min,max]` или `null`), `user_auth`. Фильтр активных листингов: цена существует, `refunded` не true, `buyer` не существует, `export_at` существует; необязательные `gift_name`, `model`, `backdrop`, `pattern`, `asset` (`TON`/`TONNEL`/`USDT`). Значения: точное (с редкостью в скобках), `{"$regex": …}` или `{"$in": […]}`. Ключи сортировки: `message_post_time`, `export_at`, `price`, `gift_num`, `modelRarity`, `backdropRarity`, `symbolRarity`, `rarity`, `gift_id` (смысл двух последних неизвестен) [R] |
| Поля подарка | `gift_num`, `gift_id` (внутренний ID Tonnel ≠ `gift_num`), `name`, `model`, `symbol`, `backdrop`, `asset`, `price`, `status`, `limited`, `auction`, `export_at`, `availabilityIssued`, `availabilityTotal`, `message_in_channel`, `bundleData`, `premarket` [R, пересказ примера `getGifts`; в фильтре «символ» зовётся `pattern`] |
| Продажи | `saleHistory()` (можно с пустым auth) [R: имя]; путь [?] |
| Покупка | `buyGift(gift_id, price, authData, receiver?, anonymously=False, showPrice=False)` [R]. Итог к оплате = `price × 1.1` (заявлено tonnelmp). Путь, тело [?] |
| Листинг | `listForSale(gift_id, price, authData)`, `cancelSale`, `unlockListing`, `returnGift`, `withdraw` [R: имена/параметры]; пути [?] |
| Баланс / профиль | `info()` [R: имя; содержимое не подтверждено] |
| Пагинация | `page` + `limit` ≤ 30 [R] |
| Лимиты | кроме `limit` ≤ 30 не установлены [?] |
| Формат цен | `price` в TON **без** 10% комиссии покупателя (заявлено tonnelmp) [R]; единицы (TON дробью / nanoTON) [?] |
| WebSocket событий | не подтверждён ни одним прочитанным источником (источник задания — topcvetok, не прочитан) [?] |
| Защита от ботов | README boostNT: `requests/httpx` не работают, нужен `curl_cffi` с `impersonate="chrome"`, браузерные заголовки и случайный User-Agent; механизм не раскрыт [R]. tonnelmp: `fake_useragent`, исправления 403, прокси [R] |
| Комиссии | см. §5, не проверено |

## 4. Telegram (MTProto) — независимый сигнал оценки

`payments.getUniqueStarGiftValueInfo(slug)` — только для пользовательской сессии, слой ≥ 212; возвращает оценку в **фиатной** валюте аккаунта и статистику перепродаж. Подробности — `docs/research/SUMMARY.md` §3. В `pricing/tg_value.py` использовать как дополнительный сигнал.

## 5. Комиссии (все цифры — заявлено, НЕ проверено)

| Маркет | Покупка | Продажа | Вывод | Источники и противоречия |
|---|---|---|---|---|
| Portals | 0% [заявлено в задании I и постом канала «0% fee on Portals»] | 5% (задание I; статьи: ~5%) / 2.5% (vc.ru, статья 2025) | 0.1 TON (задание I) | цифры расходятся (5% vs 2.5% vs 0%); в README Portals-API/portalsmp комиссий нет |
| Tonnel | +10% к цене в API (README tonnelmp: `buyGift = price × 1.1`) | ~3–4% (статья dev.to) | не установлено | «10% покупки» — из README клиента; статья описывает только комиссию продавца |
| MRKT | не установлено | ~5% (статья) / 2% (другая статья того же издателя) / «самые низкие» (третья) | не установлено | статьи dev.to — партнёрский контент, внутри одного источника цифры расходятся |

Вывод: `pricing/fees.py` должен брать комиссии из конфигурации с пометкой «не проверено», а чистая прибыль до проверки — показываться с предупреждением. Проверка на практике (минимальная покупка/продажа вручную владельцем проекта, сверка списаний) — задача человека; агент покупок не делает.

## 6. Временный бюджет запросов (решение проекта, не данные маркетов)

Реальные лимиты маркетов не известны. До измерения (Этап 9.4) на Этапе 2 принимаем консервативно: **не чаще одного запроса списка листингов на маркет раз в 5 секунд**, не более 1 запроса в секунду суммарно на маркет, на 429/5xx — экспоненциальный backoff с jitter, таймаут 10 с. Значение пересмотреть после замеров; зафиксировано в `docs/DECISIONS.md` (D-008).

## 7. Что не установлено и блокирует клиенты (список для Этапа 2)

- Пути и тела запросов покупки/листинга/баланса: Portals, MRKT, Tonnel.
- Схемы ответов (поля, единицы цены) — получить записью фикстур на Этапе 2 под присмотром владельца.
- Срок жизни токенов, лимиты, механизм защиты Tonnel.
- Точный `base URL` Portals (`portal-market.com` vs `portals-market.com`).
