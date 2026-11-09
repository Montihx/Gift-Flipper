# boostNT/MRKT-API

> Источник: исходники, клон от 2026-11-09, коммит `580378a250a1f18fa75b7c31c4168e908e68fafc`. В репозитории один файл — `README.md` (213 строк); весь «код» здесь — примеры на Python внутри README. Ссылки вида `README:N` указывают на строку README в этом коммите. Живых запросов не было, ничего не запускалось.
> Для сверки прочитан клон TheBrainAir/amrkt (коммит `2a4dbf5`, 2026-03-22): `amrkt/client.py`, частично `amrkt/models.py` и `README.md` — только как текст.

- Ссылка: https://github.com/boostNT/MRKT-API
- Язык / стек: только документация на русском (README) с примерами на Python: Pyrogram (в тексте «куриграм», т.е. форк Kurigram) + `curl_cffi` (README:63-69, 128-133). Telethon упомянут как альтернатива (README:59-61).
- Лицензия: файла LICENSE нет, в README лицензия не указана. Значит, текст и примеры не копируем; описание эндпоинтов берём и переписываем.
- Последний коммит / активность: 2026-03-30, `580378a` «fix 429». Всего 8 коммитов (история полная, меньше лимита клона 50): первый 2025-05-31, основной текст 2025-05-31…2025-06-03, затем 2026-02-07 (убран контакт автора) и 2026-03-30.
- Звёзды / форки: не установлено (api.github.com закрыт). Коммиты: 8.
- Доверие: среднее. Только документация, бинарников и исполняемых файлов нет, признаков малвари нет. Покрыто всего 2 эндпоинта; формат ответов не показан.

## Что делает (2–3 предложения)

Неофициальная документация API маркета MRKT (`@mrkt`, `api.tgmrkt.io`). Описывает ровно два запроса: список подарков на продаже (`POST /api/v1/gifts/saling`) с фильтрами и курсорной пагинацией и получение токена (`POST /api/v1/auth` с `initData` из Mini App). Есть «полный рабочий код» — пример на Pyrogram + `curl_cffi`.

## Как устроено

### Источник данных

- Только HTTP polling, `POST`. WebSocket, частота опроса, лимиты в README не описаны.
- Базовый URL: `https://api.tgmrkt.io/api/v1` (README:135, константа `MARKET_API_URL`).

### Полный перечень путей (дословно из README)

| Назначение | Метод и путь | Тело | Заголовки | Ответ | Источник |
|---|---|---|---|---|---|
| auth | `POST https://api.tgmrkt.io/api/v1/auth` | `{"data": init_data}` | в примерах никаких (README:99, 200) | JSON; из него берут ключ `token` (`rj.get('token', None)`); пример тела ответа в README НЕТ (только скриншот DevTools, README:120) | README:53-57, 96-104, 198-205 |
| saling (подарки на продаже) | `POST https://api.tgmrkt.io/api/v1/gifts/saling` | JSON-фильтр, см. ниже | `Authorization: <token>`, `Referer: https://cdn.tgmrkt.io/` | JSON; используются ключи `gifts` (список) и `cursor`; схема объекта подарка и пример ответа в README НЕТ | README:6-9, 145, 164-174 |
| buy | — | — | — | — | в README не найдено |
| sell / sale | — | — | — | — | в README не найдено |
| balance | — | — | — | — | в README не найдено |
| inventory | — | — | — | — | в README не найдено |
| history | — | — | — | — | в README не найдено |
| feed | — | — | — | — | в README не найдено |
| офферы | — | — | — | — | в README не найдено |

Пути для buy/sale/balance/inventory/feed/offers есть в amrkt — см. таблицу расхождений ниже. Эндпоинт `history` не найден ни в README, ни в `amrkt/client.py`.

### Тело `gifts/saling` (README:14-29, дословно)

```python
json_data = {
    "collectionNames": [],
    "modelNames": [],
    "backdropNames": [],
    "symbolNames": [],
    "ordering": "Price",
    "lowToHigh": True,
    "maxPrice": None,
    "minPrice": None,
    "mintable": None,
    "number": None,
    "count": 20,
    "cursor": '',
    "query": None,
    "promotedFirst": False,
}
```

Пояснения автора (README:34-47):
- `collectionNames`, `modelNames`, `backdropNames`, `symbolNames` — списки названий; `modelNames` работает и без `collectionNames`.
- `ordering`: `Price` | `ModelRarity` | `BackgroundRarity` | `SymbolRarity` | `None` (= по времени выставления).
- `lowToHigh` — по возрастанию.
- `maxPrice` / `minPrice` — «Макс./Мин. цена подарка». **Единицы не указаны.**
- `mintable` — «можно ли вывести подарок в блокчейн (наверное)».
- `number` — номер подарка.
- `count` — максимум подарков в ответе, **«лимит - 20»** (README:44).
- `cursor` — для первой страницы пустая строка `''`; для следующих — значение ключа `cursor` из предыдущего ответа; «его значение может быть None, если в первом ответе вы получили меньше подарков, чем указали в лимите» (README:45).
- `query`, `promotedFirst` — «Неизвестно».

Пример фильтра: `collectionNames=['Lunar Snake']`, `modelNames=['Albino']` (README:148-149).

### Пагинация

Курсорная (README:45, 169-174): `cursor = rj['cursor']` → подставить в тот же JSON → повторить запрос. Признак конца — `cursor` = `None` (README:45). Размер страницы ≤ 20 (README:44). Отдельного offset нет.

### Авторизация (README:51-123, 180-207)

1. Получить `initData`: через Pyrogram `messages.RequestAppWebView(peer=@mrkt, app=InputBotAppShortName(bot=@mrkt, short_name='app'), platform='android')`, затем из `web_view.url` вырезать часть между `tgWebAppData=` и `&tgWebAppVersion` и `unquote` (README:80-94, 182-196).
2. `POST /api/v1/auth` с `{"data": init_data}` → `token` (README:96-104).
3. Альтернатива: открыть веб-Telegram, F12 → Network, найти ответ `/api/v1/auth` и скопировать токен (README:118).
4. Использование: заголовок `Authorization` со значением токена **без префикса** (`Bearer` не используется) (README:145).
5. Срок жизни: «Время действия токена неизвестно, но точно более суток» (README:123). Обновления токена при 401 в примере нет.
6. Примечание (README:60-61): из России может понадобиться прокси для Telegram-сессии; в Kurigram нет MTProto-прокси, только http/socks5.

### Заголовки Referer / Origin

- `Referer: https://cdn.tgmrkt.io/` — добавлен коммитом `580378a` от 2026-03-30 с сообщением **«fix 429»** (до этого заголовок был только `{'Authorization': token}`). Автор связывает отсутствие `Referer` с ответом 429. Источник: README:145 + `git log -p`.
- `Origin` в README не упоминается (в README не найдено).
- `User-Agent` не задаётся; используется `curl_cffi.requests` без параметра `impersonate` (README:133, 164) — т.е. TLS-имитация в примере не включена явно.

### Единицы цен

В README не указаны (ни для `minPrice`/`maxPrice`, ни для ответа). По amrkt — nanoTON (см. расхождения). Для фильтров `minPrice`/`maxPrice` единица nanoTON подтверждается только docstring'ом amrkt (`client.py:379-380`), не живым запросом.

### Soft / hard баланс

В README не найдено. Есть в amrkt: `GET /balance` → поля `soft`, `hard`, `totalHard`, `hardLocked`, `stars`, `starsFotWithdraw` (sic), `spices` и др. (`amrkt/models.py:68-80`); amrkt делит `soft` и `hard` на 1e9 (`models.py:86-93`), т.е. оба трактует как nanoTON. Чем soft отличается от hard, в коде amrkt не объяснено (только «Soft balance»/«Hard balance»).

### Остальное по шаблону

- Модель данных подарка: в README не описана (только `gifts` как список).
- Оценка/флор, комиссии: в README не найдено.
- Покупка/продажа: в README не найдено.
- Предохранители и лимиты: только `count` ≤ 20 и намёк на 429 без `Referer`. Обработки ошибок в примере нет, кроме `try/except Exception: print(e)` (README:163-176).
- Уведомления / UI, хранение состояния: нет. Pyrogram-сессия хранится в файле `main` (README:75, 138).

### Безопасность / признаки риска

- Исполняемых файлов, base64, `exec`, отправки сессии на сторонние адреса нет. Все запросы — только на `api.tgmrkt.io` и Telegram.
- В примерах `api_id`/`api_hash` — явные заглушки с пометкой «замени» (README:73-74, 136-137), не реальные секреты; значения в отчёт не переносим.
- Мелкая ошибка в первом примере: `Client('main')` создаётся без `api_id`/`api_hash` (README:75), во втором примере исправлено (README:138).

## Расхождения boostNT/MRKT-API ↔ amrkt

| Пункт | boostNT/MRKT-API (README) | amrkt (`amrkt/client.py`, если не указано иное) | Вывод |
|---|---|---|---|
| auth: заголовки | без заголовков (README:99, 200) | полный набор браузерных заголовков, включая `Origin`/`Referer` (`client.py:233-237`, `110-125`) | слать браузерные заголовки и на `/auth` |
| auth: получение bot app | `InputUser(user_id, access_hash)` из `get_users('mrkt')` (README:182-185) | `InputBotAppShortName(bot_id=peer)` от `resolve_peer('mrkt')` (`client.py:217-218`) | детали Pyrogram, суть одна: `short_name='app'`, `platform='android'` |
| Заголовок токена | `Authorization: <token>` (README:145) | `Authorization: <token>` + `Cookie: access_token=<token>` (`client.py:126-128`) | Cookie — только в amrkt; нужно ли, не проверено |
| Referer | `https://cdn.tgmrkt.io/`, добавлен как «fix 429» (README:145) | `https://cdn.tgmrkt.io/` (`client.py:120`) | совпадает |
| Origin | не указан | `https://cdn.tgmrkt.io` (`client.py:117`) | брать из amrkt |
| Прочие заголовки | нет | `Accept`, `Accept-Language`, `Sec-Fetch-*` (`same-site`, `cors`, `empty`), `Priority: u=3, i`, `Host`, случайный мобильный `User-Agent` (`client.py:13-20, 110-125`) | брать из amrkt |
| TLS-отпечаток | `curl_cffi` без `impersonate` (README:133, 164) | `impersonate="chrome124"` по умолчанию (`client.py:65, 134-135`) | использовать impersonate |
| Срок токена / 401 | «неизвестно, точно более суток» (README:123); обработки 401 нет | проверка токена пробным `saling` с `count=1` и перевыпуск при 401, один повтор (`client.py:182-203, 281-287`) | перевыпуск по 401 |
| `gifts/saling` тело | 14 полей (README:14-29) | те же 14 полей и имена (`models.py:381-398`), вызов `client.py:408` | совпадает |
| `count` | лимит 20 (README:44) | по умолчанию 20 в `search_gifts` (`client.py:364`), но в README amrkt пагинация `search_gifts` с `count=50` и выходом по `len(items) < 50` (amrkt `README.md:668-681`) | **расхождение.** Если сервер действительно режет до 20, цикл из README amrkt остановится после первой страницы. Верить лимиту 20 до проверки |
| Конец пагинации | `cursor` = `None`, если пришло меньше `count` (README:45) | `GiftList.cursor: Optional[str]` (`models.py:261-265`) | совпадает |
| `ordering` | `Price`/`ModelRarity`/`BackgroundRarity`/`SymbolRarity`/`None` | docstring: `"Price", "Date", etc.` (`client.py:377`) | значение `Date` есть только в amrkt и не подтверждено; у boostNT «по времени» = `None` |
| Единицы цен | не указаны | nanoTON: фильтры (`client.py:379-380`), продажа (`client.py:538, 551`), офферы (`client.py:625, 637`), поля `salePrice`, `salePriceWithoutFee`, `floorPriceNanoTONsByCollection`, `floorPriceNanoTONsByBackdropModel` (`models.py:179-182`) | считаем nanoTON (int) |
| Ответ auth | ключ `token` | ключ `token`, иначе `AuthenticationError`; не-200 → ошибка (`client.py:240-247`) | совпадает |
| buy | нет | `POST /gifts/buy`, тело `{"Ids": [gift_id, ...]}` (заглавная `I`), ответ — список `{userGift, price}` (`client.py:447`, `models.py:301-304`) | только amrkt |
| sell | нет | `POST /gifts/sale`, `{"ids": [...], "prices": [nanoTON, ...]}`, ответ `{ids, prices}` (`client.py:557-561`, `models.py:340-343`) | только amrkt |
| снять с продажи | нет | `POST /gifts/sale/cancel`, `{"ids": [...]}`, ответ — список id (`client.py:578-583`) | только amrkt |
| смена цены | нет | `POST /gifts/sale/change-price`, `{"ids": [...], "prices": [...]}` (`client.py:610-614`) | только amrkt |
| balance | нет | `GET /balance` (`client.py:324`); поля soft/hard/totalHard/hardLocked (`models.py:68-75`) | только amrkt |
| inventory | нет | `POST /gifts` с тем же телом, что `saling`, по умолчанию `count=50`, `lowToHigh=False` (`client.py:455-498`) | только amrkt; лимит count для `/gifts` не известен |
| return (вывод в Telegram) | нет | `POST /gifts/return`, `{"Ids": [...]}` (`client.py:513`) | только amrkt |
| history | нет | нет | в коде не найдено нигде |
| feed | нет | `POST /feed`, тело `{}`, ответ `{items: [{type: listing/sale/change_price, id, gift, amount, date}]}` (`client.py:527`, `models.py:315-335`) | только amrkt; фильтры feed неизвестны |
| офферы | нет | `POST /offers/create` `{"price": nanoTON, "giftSaleId": ...}`, ответ не JSON (`client.py:640-645`); `POST /offers/cancel?offerId=...` (`client.py:666-671`) | только amrkt |
| активности (мои офферы и т.п.) | нет | `GET /activities?offset=&count=&isActive=true` (`client.py:693-701`) — пагинация offset, не cursor | только amrkt |
| прочее | нет | `GET /me` (`client.py:312`), `GET /transactions/await` (`334`), `POST /transactions/{id}` (`347`), `GET /gifts/gift/{id}` (`421`), `GET /gifts/collections` (`431`, поле `floorPriceNanoTons`, `models.py:277`) | только amrkt |
| WebSocket | нет | нет | в коде не найдено |

## Что берём

| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| `POST /api/v1/gifts/saling`, 14 полей фильтра, значения `ordering` | `markets/mrkt.py`, `docs/MARKETS.md#mrkt` | Формат API, переписать своей моделью запроса |
| Курсорная пагинация, `count` ≤ 20, конец по `cursor is None` | `markets/mrkt.py` | Страницы по 20; дополнительно останавливаться при пустом `gifts` |
| `POST /api/v1/auth {"data": initData}` → `token`; `Authorization` без `Bearer` | `markets/mrkt.py`, Telethon-сессия | Переписать на Telethon (`RequestAppWebViewRequest`, `short_name='app'`, `platform='android'`); перевыпуск по 401 |
| `Referer: https://cdn.tgmrkt.io/` обязателен (иначе, по автору, 429) | `markets/mrkt.py` | Плюс `Origin: https://cdn.tgmrkt.io` из amrkt |

## Что НЕ берём и почему

- Текст и примеры целиком — лицензии нет.
- Синхронный `curl_cffi.requests` внутри `async def` (README:164) — блокирует цикл событий; у нас асинхронный клиент.
- Оценку срока токена «более суток» — не гарантия, полагаемся на 401.

## Открытые вопросы

- Единицы `minPrice`/`maxPrice` и цен в ответе `saling` (по amrkt — nanoTON; проверить на живом ответе).
- Схема объекта подарка в ответе `saling` (по amrkt `models.py:140-225`: `id`, `salePrice`, `salePriceWithoutFee`, …) — сверить с фикстурой.
- Действительно ли сервер режет `count` до 20 (README boostNT) или принимает 50 (пример в README amrkt).
- Нужен ли `Cookie: access_token=…` и `Origin` помимо `Referer`.
- Назначение `query`, `promotedFirst`, `mintable`; есть ли значение `ordering` `Date`.
- Есть ли эндпоинт истории продаж (history) — ни здесь, ни в amrkt не найден; кандидат — `POST /feed` с фильтром по типу `sale`.
- Лимит частоты запросов (известно только, что без `Referer` бывает 429).

## Для MARKETS.md

- Base URL: `https://api.tgmrkt.io/api/v1` — из README:135 (boostNT), совпадает с amrkt `client.py:55`.
- Auth: `POST /auth`, тело `{"data": "<initData>"}`, ответ `{"token": "..."}` — из README:53-57, 96-104. initData: `RequestAppWebView` к `@mrkt`, `short_name='app'`, `platform='android'` — из README:86-94.
- Токен: заголовок `Authorization: <token>` без `Bearer` — из README:145. amrkt дополнительно шлёт `Cookie: access_token=<token>` — из кода (amrkt `client.py:128`).
- Срок токена: неизвестен, «более суток» (оценка автора) — из README:123. Перевыпуск по 401 — из кода (amrkt `client.py:281-287`).
- Обязательные заголовки: `Referer: https://cdn.tgmrkt.io/` (добавлен как «fix 429», коммит `580378a` 2026-03-30) — из README:145. `Origin: https://cdn.tgmrkt.io`, `Sec-Fetch-Site: same-site` — из кода (amrkt `client.py:110-125`), в README boostNT нет.
- Поиск: `POST /gifts/saling`, тело `collectionNames[]`, `modelNames[]`, `backdropNames[]`, `symbolNames[]`, `ordering` (`Price`|`ModelRarity`|`BackgroundRarity`|`SymbolRarity`|`null`=по времени), `lowToHigh`, `maxPrice`, `minPrice`, `mintable`, `number`, `count` (≤ 20), `cursor` (`""` для первой страницы), `query`, `promotedFirst` — из README:14-47. Ответ `{gifts: [...], cursor: str|null}` — из README:166-171.
- Пагинация: курсорная; `cursor=null` — конец — из README:45. Расхождение: README amrkt использует `count=50` (amrkt `README.md:674`) — не подтверждено.
- Цены: nanoTON (int) — из кода amrkt (`client.py:379-380, 538, 625`; `models.py:179-182`); в README boostNT единицы не указаны.
- Баланс: `GET /balance` → `soft`, `hard`, `totalHard`, `hardLocked` (nanoTON), `stars`, `starsFotWithdraw` — из кода amrkt (`client.py:324`, `models.py:68-75`); в boostNT нет.
- Buy `POST /gifts/buy {"Ids": [...]}`; sale `POST /gifts/sale {"ids", "prices"}`; cancel `POST /gifts/sale/cancel {"ids"}`; change-price `POST /gifts/sale/change-price {"ids","prices"}`; inventory `POST /gifts` (тело как у saling); return `POST /gifts/return {"Ids"}`; feed `POST /feed {}`; offers `POST /offers/create {"price","giftSaleId"}`, `POST /offers/cancel?offerId=`; activities `GET /activities?offset&count&isActive` — всё из кода amrkt (`client.py:447-701`), в boostNT отсутствует.
- History продаж: в коде не найдено (ни boostNT, ни amrkt).
- TLS: `curl_cffi` (`impersonate="chrome124"` в amrkt `client.py:65`; в README boostNT без impersonate).
