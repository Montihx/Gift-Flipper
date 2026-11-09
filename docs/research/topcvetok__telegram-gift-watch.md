# topcvetok/telegram-gift-watch

Источник: исходники, клон от 2026-11-09, коммит `05f658af83f078f2d4747caf6c7a260781e3536e` (HEAD, 2026-11-01). Старую версию отчёта заменили целиком: её делали без доступа к коду, и подтверждённых фактов в ней не было. Ниже `файл:строка` указывает на HEAD. Где сказано `git show b0e81f2^:<файл>`, речь о версии до коммита b0e81f2 (29.10.2026), в котором прямой MRKT API заменили на партнёрский API Swift Gifts. Живых запросов не делали. Ни один ответ API здесь не помечен как «проверено на живом ответе».

- Ссылка: https://github.com/topcvetok/telegram-gift-watch
- Язык / стек: Python 3.9+ (README.md:48), `curl_cffi==0.13.0` и `Pillow==11.3.0` (requirements.txt:1-2), stdlib `sqlite3`/`urllib`. Работает на GitHub Actions как «вечный» воркер (.github/workflows/gift-watch.yml). Mini App: статический `webapp/index.html` на GitHub Pages. Бэкенд истории и настроек: Supabase Edge Function на Deno/TypeScript (supabase/functions/gift-watch-history/index.ts) и таблицы из supabase/schema.sql.
- Лицензия: **нет**. Файла LICENSE в репозитории нет, в README (135 строк) упоминаний лицензии тоже нет (проверено grep по `licen|MIT`). Код копировать нельзя (AGENTS.md §4 п.4), берём только идеи и описания API.
- Последний коммит / активность: 2026-11-01 00:05 +0300, «Explain Portals listing rejections». В неглубоком клоне самый ранний коммит датирован 2026-10-12. По README.md:3 проект начат 11.10.2026. Активная разработка шла около 3 недель, автор один (`n1kseeman`).
- Звёзды / форки / коммиты: звёзды и форки не установлены (api.github.com закрыт). Коммитов ≥50 (неглубокий клон, упёрлись в лимит 50).
- Доверие: **среднее–высокое как источник идей**. Код чистый и читаемый, есть ~20 тестовых файлов, ничего не обфусцировано. `base64`, `exec`, `eval`, `subprocess` и скачивания бинарников grep не нашёл. Секретов в репозитории нет: все токены берутся из GitHub Secrets (gift-watch.yml:45-71). Что настораживает:
  - события Tonnel берутся **не с домена Tonnel**, а со стороннего `gifts.coffin.meme` (tonnel_watch.py:29-30);
  - GitHub Actions используется как круглосуточный сервер: workflow сам ставит себя в очередь (gift-watch.yml:142-151);
  - в истории есть удалённый workflow `temporary-socks-proxy.yml` (коммит 8de2bf6, удалён в 6d51bf6). Он поднимал SOCKS-прокси на раннере и пробрасывал его наружу через `free.pinggy.io` для входа в MRKT. Это не малварь, но практика, которую мы не повторяем.

## Что делает (2–3 предложения)

Мониторит листинги Tonnel, Portals и MRKT (MRKT сейчас идёт через партнёрский API Swift Gifts) и присылает в Telegram сигналы «оффер ниже устойчивого флора» с расчётом прибыли. Ещё он ловит свежие улучшения подарков с заданными фонами. Сам ничего не покупает (README.md:3). Когда лот продан, уже отправленное уведомление редактируется в карточку «ПРОДАНО». Есть многопользовательский режим с личными настройками в Mini App и ежедневный отчёт.

## Как устроено

- **Источник данных:**
  - **Tonnel.** Каталог: `POST https://gifts2.tonnel.network/api/pageGifts`, опрос (tonnel_watch.py:28, 117-138). События: WebSocket `wss://gifts.coffin.meme/api/marketplace/ws` и REST-догонка `GET https://gifts.coffin.meme/api/marketplace/events` (tonnel_watch.py:29-30, 789-852).
  - **Portals.** `GET https://portal-market.com/api/nfts/search`, `/collections`, `/nfts/{id}`, опрос каждые 5 с (portals_watch.py:45, 155-190, 746-774; config.json:33).
  - **MRKT.** Сейчас: `POST https://partners.swiftgifts.tg/api/actions/services/mrkt` раз в 5 с (mrkt_watch.py:30, 536-549; config.json:39). До 29.10: `POST https://api.tgmrkt.io/api/v1/feed` и `/gifts/saling` (`git show b0e81f2^:mrkt_watch.py`:27, 181-189, 432-437).
  - **Курс TON/RUB:** CoinGecko `simple/price?ids=the-open-network&vs_currencies=rub`, кэш 1 ч (tonnel_watch.py:31, 855-873).
  - **Монохром:** `GET https://app.clue.tg/api/mono/resolve` (special_traits.py:12).
  - **Улучшения:** каталог названий `https://api.changes.tg/gifts`. Наличие номера проверяется через HEAD `https://nft.fragment.com/gift/{slug}-{n}.small.jpg`, атрибуты и владелец парсятся из HTML `https://t.me/nft/{Slug}-{n}` (upgrade_watch.py:31-33, 78-98, 150-198).
- **Авторизация:**
  - Tonnel: без авторизации, `user_auth: ""` в теле (tonnel_watch.py:133).
  - Portals: публичные маршруты без токена. Необязательный заголовок `authorization` берётся из `secrets.portals_token`, если он задан (portals_watch.py:57-66, 747). Тест подтверждает, что без токена заголовка нет (test_portals_watch.py:67-76).
  - MRKT (старая схема): `authorization: <token>` + `cookie: access_token=<token>`, где `MRKT_TOKEN` — токен пользовательской сессии Mini App. Как его получали, в коде не найдено. README той версии говорит только, что токен «получается только после входа реального пользователя в Mini App @mrkt/app» (diff b0e81f2 README).
  - MRKT (новая схема): `x-api-key: SWIFT_API_KEY` (mrkt_watch.py:48-53).
- **Модель данных подарка** (общая, приводится к формату Tonnel): `gift_id, gift_num, name, model, backdrop, symbol, price (Decimal TON), status="forsale", asset="TON", auction, dutchAuctionData, premarketData, underLoan`. Для Portals и MRKT добавляются `collection_id`/`listed_at` и `listing_url`/`telegram_url`/`image_url` (portals_watch.py:136-152; mrkt_watch.py:236-254).
- **Оценка/флор:** разобрана в п.1–3 ниже.
- **Комиссии:** раздел «Комиссии» ниже.
- **Покупка/продажа:** нет. Торговые маршруты не вызываются (README.md:34).
- **Предохранители и лимиты:**
  - Tonnel: до 3 попыток с паузой 2 и 4 с. Повтор при 403/5xx. При 429 ждёт `retry-after` (по умолчанию 300 с, минимум 60), цикл сразу прерывается (tonnel_watch.py:47-50, 89-114, 931-932). Пауза между коллекциями 1,2 с (config.json:60). Не более 2 новых запросов книг вариантов за цикл и за событие (config.json:68-69).
  - Portals: не чаще 1 запроса в 1,2 с (portals_watch.py:47, 74-76). При 429 ждёт `retry-after` (по умолчанию 30, минимум 5, не больше 300), обработка цикла прерывается после первого же 429 (portals_watch.py:51-54, 719-722, 762).
  - Swift: 1 запрос в 1,05 с. 429 → по умолчанию 60 с; 401/403/402 → останов (mrkt_watch.py:34, 56-94).
  - Фильтры лотов: исключаются аукционы, премаркет, залоговые лоты (`underLoan`), лоты с будущим `unlocks_at`/`nextResaleDate` и цены выше `max_lot` (2000 ₽) (tonnel_watch.py:260-271; portals_watch.py:124-126; mrkt_watch.py:227-235).
- **Уведомления / UI:** Telegram Bot API `sendMessage` и `editMessageText` в HTML-разметке. Большое превью `t.me/nft/<slug>` над текстом, inline-кнопка «Открыть оффер» (bot.py:143-201). Текст карточки строится в alert_format.py:37-120. Mini App на GitHub Pages с тремя вкладками (README.md:27). Настройки приходят в бота через `web_app_data` (settings_bot.py:216-219), доступ для других пользователей — по `/join <код>` (settings_bot.py:203-204).
- **Хранение состояния:** SQLite `state.sqlite3` и `settings.sqlite3` в режиме WAL (tonnel_watch.py:957-963). Между запусками Actions база живёт в кэше Actions, перед сохранением делается checkpoint (gift-watch.yml:34-43, 115-128). История и настройки дублируются в Supabase (п.9).

---

## Задание A

### A1. Флор по коллекции, модели и фону; минимум сопоставимых; «слишком разбросанные цены»

Ядро — `floor_evidence()` (tonnel_watch.py:274-318). Portals и MRKT вызывают эту же функцию через `best_score()`, подменяя только резерв расходов (portals_watch.py:523-528, 652-653; mrkt_watch.py:312-317, 498-500).

Алгоритм для одного лота `item` и «книги» сопоставимых `book`:
1. Лот должен пройти `eligible()` и стоить не больше `max_lot` (по умолчанию 2000 ₽, пересчитанные в TON по курсу) (tonnel_watch.py:275-280; config.json:4).
2. `others` — цены всех eligible-лотов книги **кроме самого лота**, по возрастанию (tonnel_watch.py:281-288).
3. Если `len(others) < min_comparables`, сигнала нет (tonnel_watch.py:289-291).
4. `cluster = others[:min_comparables]`, `next_floor = cluster[0]`, то есть флор равен **минимальной цене среди остальных**, а не медиане (tonnel_watch.py:292-293).
5. **Слишком разбросанные цены:** `cluster[-1] > next_floor * (1 + max_spread)` → сигнала нет (tonnel_watch.py:294-296).
6. Если `next_floor < min_floor` (по умолчанию 1000 ₽ → TON), сигнала нет (tonnel_watch.py:297-299; config.json:5).
7. `discount = (next_floor − price)/next_floor`, `resale = next_floor − undercut_ton (0.01)`, `net = resale·(1 − cost_fraction) − fixed_cost_ton (0)`, `profit_ton = net − price`, `roi = profit_ton/price` (tonnel_watch.py:300-308).

Константы по основаниям (config.json):

| Основание | Книга | Мин. сопоставимых | Макс. разброс | Размер книги | Кэш книги (Tonnel) |
|---|---|---|---|---|---|
| Вся коллекция | `gift_name` | `min_comparables` = **5** (:61) | `floor_cluster_max_spread_fraction` = **0.08** (:62) | `floor_limit` = 12 (:56) | `collection_floor_cache_seconds` = 900 (:57) |
| Модель | `gift_name` + `model` | `variant_min_comparables` = **3** (:63) | `variant_floor_cluster_max_spread_fraction` = **0.2** (:64) | `variant_floor_limit` = 10 (:65) | `variant_cache_seconds` = 1800 (:66) |
| Фон | `gift_name` + `backdrop`, только разрешённые фоны | 3 | 0.2 | 10 | 1800 |

- Подмена порогов для модели и фона: tonnel_watch.py:367-371. Фоны по умолчанию: `Black, Onyx Black, Gunmetal, Midnight Blue` (tonnel_watch.py:39-44; runtime_settings.py:52). Пользователь может выбрать любые из 80 названий (runtime_settings.py:32-49). Суффикс редкости `" (1%)"` отрезается регуляркой (tonnel_watch.py:68).
- `best_score()` прогоняет все три основания и возвращает результат с максимальным `(profit_rub, discount)` (tonnel_watch.py:358-409). Каждое основание включается отдельно. **Флор коллекции по умолчанию выключен:** `collection_basis_enabled: false` (config.json:6). Модель и фон включены (:7-8).
- Пример из тестов (test_tonnel_watch.py:65, 85-87): книга `[3.57, 3.57, 3.58, 3.59, 3.60, 3.62]` считается устойчивой. Книга `[3.57, 3.58, 3.90, 4.10, 5.00]` неустойчива: 5.00 > 3.57·1.08.
- Для Portals тот же критерий повторён в `stable_floor()` (portals_watch.py:334-350). «Floor модели по площадкам» в карточке — это просто `min` без проверки кластера (`lowest_floor`, portals_watch.py:353-362, 386-390), и для него хватает одного другого лота (README.md:19).

### A2. Правило «≥15% ниже флора и ≥5 соседних объявлений»

Правило реализовано в `score()` (tonnel_watch.py:321-337) поверх `floor_evidence()`. Проверки:
- `discount ≥ min_discount_fraction` = **0.15** (config.json:75);
- `profit_ton > 0`;
- `profit_rub ≥ min_scenario_profit_rub` = **100 ₽** (config.json:25);
- `roi ≥ min_roi_fraction` = **0.15** (config.json:26).

«≥5 соседних» — это `min_comparables = 5` (config.json:61) плюс кластер в пределах 8%. Такое требование действует **только для основания «вся коллекция»**, а оно по умолчанию выключено. Для модели и фона нужно ≥3 соседних и разброс ≤20%. README.md:15 описывает правило упрощённо и об этом не говорит.

Значения по умолчанию в `runtime_settings.py`. Через Mini App меняются только:
- `max_lot_rub`, `min_floor_rub`, `upgrade_min_floor_rub`, в рублях или TON (runtime_settings.py:9-13, 187-196, 315-340, 577-582);
- включение площадок и оснований (:16-30, 197-206);
- `beautiful_number_max_distinct_digits` (1–10), `monochrome_min_score` (0–100), `monochrome_max_floor_premium_percent` (0–100), `daily_report_hour` (0–23) (:53-64);
- наборы фонов и белые/чёрные списки (:66-71, 210-221, 280-291).

`min_discount_fraction`, `min_comparables`, разбросы, `min_roi` и `min_scenario_profit_rub` **из Mini App не меняются**: они читаются только из config.json. Хранение: `runtime_settings_by_chat(chat_id, key, value, updated)`, а `effective_config()` накладывает эти значения на config.json для каждого чата (runtime_settings.py:113-145, 169-222).

### A3. Медиана продаж за 24 ч: откуда берутся продажи на каждом маркете

`apply_sales_evidence()` (tonnel_watch.py:545-587) и `sales_metrics()` (:471-542) работают так:
- Продажи складываются в одну таблицу `tonnel_sales(event_id PK, gift_id, gift_name, model, backdrop, symbol, price, source, occurred)`. Хранятся 2 суток (tonnel_watch.py:443-456).
- Выборка: продажи за последние 86400 с по тому же основанию, что и сигнал (вся коллекция, `model=` или `backdrop=`) (tonnel_watch.py:483-508).
- Если продаж ≥ `sales_confirmation_min_count` = **3** (config.json:70), то `resale = min(resale_по_флору, медиана)`, прибыль и ROI пересчитываются, и сигнал отбрасывается, если они ниже порогов. Подтверждённый монохром от этой проверки освобождён (tonnel_watch.py:553-576).
- Медиана классическая: при чётном числе берётся среднее двух средних значений (tonnel_watch.py:460-468).
- Ликвидность по числу продаж коллекции: ≥8 «высокая», ≥3 «средняя» (config.json:71-72; tonnel_watch.py:578-585). Дальше `apply_activity_evidence()` её перезаписывает по формуле `score = sales·3 + listings + price_changes·2 + other` с порогами 30 и 10 (market_data.py:63-101; config.json:73-74).

Источники продаж по маркетам:
- **Tonnel:** события `sale.completed` из WebSocket и REST coffin.meme. Используются `data.price`, `data.asset == "TON"`, `data.gift.{gift_id, gift_name, model, backdrop, symbol}`, `eventId`, `occurredAt` (tonnel_watch.py:427-457).
- **MRKT, сейчас:** Swift `POST /api/actions/services/mrkt?page=0&limit=20` с телом `{"type":"buy"}`. Тип `buy` превращается в `Sale` (mrkt_watch.py:33, 112-115, 183-211, 536-549). Цена берётся из `normalized.price.nano` или из `seller_price_ton`/`sale_price_ton`/… ×1e9, затем `/1e9` (mrkt_watch.py:142-148, 204, 320-346). Пишется с `source="mrkt"`.
- **MRKT, до 29.10:** `POST https://api.tgmrkt.io/api/v1/feed` с `type: ["Sale","Listing","ChangePrice"]`, `amount` в nanoTON (`git show b0e81f2^:mrkt_watch.py`:115-129, 233-260).
- **Portals:** отдельные продажи в `tonnel_sales` **не попадают** и в медиане не участвуют. В ликвидность добавляется только агрегат `sales_24h_count` из `GET /api/collections?search=<name>&limit=10` (portals_watch.py:246-287, 499; market_data.py:198-199). Статус `sold` у `/nfts/{id}` нужен только для смены карточки на «ПРОДАНО» (portals_watch.py:193-211).
- Исчезновение лота продажей не считается (README.md:13, 21).

### A4. «Красивые номера» и монохром

- **Красивый номер** (special_traits.py:24-36): `len(set(str(gift_num))) ≤ beautiful_number_max_distinct_digits`. По умолчанию 3 (config.json:10), допустимо от 1 до 10 (runtime_settings.py:60). Это не самостоятельный сигнал, а **ярлык к уже прибыльному сигналу по флору модели**. Если сработало только основание «модель», но оно выключено в настройках, результат помечается `_requires_special_basis` и проходит лишь при наличии номера или монохрома (tonnel_watch.py:395-401; special_traits.py:96, 120-125).
- **Монохром (Clue):**
  - Запрос: `GET https://app.clue.tg/api/mono/resolve?url=<slug>`. `slug` — название коллекции без небуквенно-цифровых символов в нижнем регистре, затем `-<номер>`, например `evileye-42`. Заголовок `accept: application/json`, `impersonate="chrome"`, таймаут 12 с. Ответ — JSON с полем `score` от 0 до 100, иначе ошибка (special_traits.py:12, 15-21, 39-54).
  - Порог `monochrome_min_score` = **80** (config.json:21).
  - Кэш по slug в таблице `gift_special_traits`: результат хранится 30 дней (`monochrome_cache_seconds` = 2592000), неудачный запрос повторяется не раньше чем через 1 ч (`monochrome_retry_seconds` = 3600) (special_traits.py:57-87; config.json:23-24). Неизвестный результат монохромом не считается (README.md:40).
  - Ослабленное правило для монохрома: цена может быть до **+15%** выше устойчивого флора модели (`monochrome_max_floor_premium_percent`, config.json:22). Скидка, прибыль и ROI тогда не требуются, а `max_lot`, `min_floor` и требование кластера остаются (tonnel_watch.py:340-355, 402-407, 564; README.md:42).
- **Можно ли считать монохром самим:** в этом коде **не найдено**, он целиком полагается на Clue. По README.md:40 Clue сравнивает доминирующий цвет модели с градиентом фона по перцептивному цветовому расстоянию. Задел для своего расчёта в репо есть: `classify_backdrop()` (upgrade_watch.py:127-147) усредняет пиксели 4×4 в четырёх углах картинки `nft.fragment.com/gift/{slug}-{n}.small.jpg` и сравнивает евклидово расстояние в RGB с целевыми цветами `Black (14,15,15)` и `Onyx Black (49,54,56)`, порог ≤10 (:35-38). Отсюда понятно, что фон по картинке Fragment определить можно. Для монохрома нужен ещё доминирующий цвет модели (центральная область без фона) и перцептивная метрика (ΔE в Lab). Это наша оценка, в коде её нет.

### A5. Tonnel: WebSocket событий

- **Адрес:** `wss://gifts.coffin.meme/api/marketplace/ws`. REST-догонка: `GET https://gifts.coffin.meme/api/marketplace/events?after=<eventId>&limit=100` (tonnel_watch.py:29-30, 798-801). Это **сторонний домен, не `tonnel.network`**. В README.md он не назван (там просто «поток событий» Tonnel). Кто держит coffin.meme, из кода не видно.
- **Протокол:** подписочных сообщений нет. Клиент делает `requests.Session(impersonate="chrome").ws_connect(url, timeout=20)` и читает кадры `socket.recv()`. Каждый кадр — один JSON-объект события (tonnel_watch.py:834-841). После (пере)подключения сначала догоняются события с курсора `tonnel_stream_state.cursor`: читаются страницы `{"events":[…], "nextAfter":"…"}`, пока страница не станет меньше 100 событий или курсор не перестанет меняться (tonnel_watch.py:789-811). При ошибке переподключение через 3 с, при 429 ожидание до 300 с (:843-850).
- **Формат события** (код и фикстуры test_tonnel_watch.py:27-47, 485-558):
  ```
  {"eventId": str, "type": "listing.created" | "listing.price_changed" | "sale.completed" | "premarket.listing_created" | …,
   "occurredAt": ISO-8601,
   "data": {"gift": {"gift_id", "gift_num", "gift_name", "model", "backdrop", "symbol"},   // атрибуты с "(N%)"
            "price": number (TON), "asset": "TON", "sale_type": "FIXED" | "DUTCH" (у listing.created),
            "previous_price": number (у price_changed), "source": "FIXED" (у sale.completed)}}
  ```
  Как лот берутся `listing.created` с `sale_type == "FIXED"` и `listing.price_changed`, только при `asset == "TON"` (tonnel_watch.py:658-681). Прочие типы, где есть слово `listing`, засчитываются как delisting в активности (:684-705). Дедупликация идёт по `eventId` в таблице `tonnel_events` со сроком 8 суток (:722-730, 779-784).
- **Что имитируется (REST `pageGifts`):** заголовки `accept: */*`, `accept-language: ru-RU,ru;q=0.9,en;q=0.8`, `content-type: application/json`, `origin: https://market.tonnel.network`, `referer: https://market.tonnel.network/` (tonnel_watch.py:32-38). TLS/HTTP-отпечаток Chrome даёт `curl_cffi` с `impersonate="chrome"` (:93-96). **Cookies не используются**, User-Agent явно не задаётся, его подставляет curl_cffi. По README обычный HTTP-клиент получает 403 (README.md:32, 61). На 403 код делает ещё до 2 попыток (:106, 112-113). Для WebSocket отдельных заголовков нет, работает только отпечаток сессии curl_cffi.
- **Тело `pageGifts`** (tonnel_watch.py:117-138): `{"page":1, "limit":N, "sort": "<JSON-строка>", "filter": "<JSON-строка>", "price_range": null, "user_auth": ""}`. Фильтр: `{"price":{"$exists":true}, "refunded":{"$ne":true}, "buyer":{"$exists":false}, "export_at":{"$exists":true}, "gift_name":<name>, "asset":"TON"}` плюс `{"model":…}` или `{"backdrop":…}`. Сортировки: `{"price":1,"gift_id":-1}` для книг и `{"message_post_time":-1,"gift_id":-1}` для новых лотов. Ответ — список (иначе «Tonnel изменил схему»). Поля лота: `gift_id, gift_num, name, model, backdrop, symbol, price, asset, status ("forsale"), auction, dutchAuctionData, premarketData, underLoan` (:260-271; test_tonnel_watch.py:10-24).
- **.github/workflows/tonnel-connectivity.yml:** ручной `workflow_dispatch`, ubuntu-latest, Python 3.12, `pip install -r requirements.txt`, затем один вызов `fetch_collection("Plush Pepe", {"price": 1}, 1)` и печать числа строк (:1-27). Это проба того, что `pageGifts` отвечает с IP раннера GitHub при имитации Chrome. Других обходов (прокси, cookies) в нём нет.
- Ссылка на лот: `https://t.me/tonnel_network_bot/gift?startapp=<gift_id>` (tonnel_watch.py:590-591).

### A6. Portals: публичные маршруты, частота, базовый URL, формат

- **Базовый URL: `https://portal-market.com/api`** (без «s»), `origin`/`referer` `https://portal-market.com` (portals_watch.py:45, 57-66). Вариант `portals-market.com` в коде не встречается.
- **Маршруты без авторизации (все GET):**
  - `/nfts/search`. Параметры `offset=0`, `limit` (1–20), `sort_by` (`"price asc"` | `"listed_at desc"`), `status=listed`, затем `collection_ids=<uuid>` или `filter_by_collections=<name>`, необязательные `filter_by_models`, `filter_by_backdrops` (portals_watch.py:155-183). Ответ: `{"results":[…]}`.
  - `/collections?search=<name>&limit=10` → `{"collections":[{"id","name","sales_24h_count",…}]}`. Совпадение по имени ищется без учёта регистра. Используется для `collection_id` (кэш 24 ч) и статистики (кэш `portals_stats_cache_seconds` = 60, минимум 30) (portals_watch.py:214-287; config.json:36).
  - `/nfts/{id}` → объект лота с `status` (`"sold"`) и `price` (portals_watch.py:186-211).
  - README.md:34 подтверждает, что эти маршруты работают без токена.
- **Частота:** цикл раз в `portals_poll_seconds` = **5 с** (минимум 3) (config.json:33; portals_watch.py:749). Каждый цикл: 1 запрос новых лотов (`listed_at desc`, `portals_feed_limit` = 20) и проверка «продано» по `portals_sold_check_batch` = 2 лотам, каждый не чаще раза в 30 с (config.json:34, 37; portals_watch.py:193-198, 680-683). Книги на каждый новый лот кэшируются на `portals_book_cache_seconds` = 120 с (config.json:35; в коде по умолчанию 20, portals_watch.py:308). Между любыми запросами не меньше 1,2 с.
- **Транспорт:** `curl_cffi`, `impersonate="chrome"`, **принудительно HTTP/1.1** (`CurlOpt.HTTP_VERSION = V1_1`), `accept-encoding: identity`, таймаут 8 с, одна попытка (portals_watch.py:69-82, 751-754).
- **Формат лота** (фикстура test_portals_watch.py:10-28; парсер portals_watch.py:113-152): `id` (строка), `tg_id` (`"EvilEye-42"`), `collection_id`, `external_collection_number` (номер), `name`, `price` (**строка, TON**, например `"8"`), `status` (`"listed"`/`"sold"`), `listed_at`, `unlocks_at` (ISO), `attributes: [{"type":"model"|"backdrop"|"symbol","value":…}]`. В отличие от Tonnel, у атрибутов нет суффикса `(N%)`.
- **Единицы цены:** TON в десятичной строке, переводится в `Decimal` без делителя. Значение `price` в выдаче сравнивается напрямую с порогами в TON (portals_watch.py:117, 611).
- Новизна лота определяется таблицей `portals_seen(id, price)`. Та же цена пропускается, подорожание только обновляет запись, первый показ или снижение цены отправляются на оценку (portals_watch.py:692-729).
- Deep link: `https://t.me/portals/market?startapp=gift_<id>` (portals_watch.py:46, 531-532).

### A7. MRKT: `/api/v1/feed` и `/api/v1/gifts/saling`

**В HEAD этих маршрутов нет.** Коммит b0e81f2 (29.10.2026) перевёл MRKT на партнёрский API Swift Gifts. После коммита 11f54b8 флор MRKT вообще не запрашивается (`mrkt_floor_enabled: false`, config.json:43), MRKT нужен только как источник событий. Прямой API описан по версии `git show b0e81f2^:mrkt_watch.py` (код был в репо с 72ef59f 13.10 по 29.10):
- **База:** `https://api.tgmrkt.io/api/v1` (:27). **Заголовки:** `accept: application/json, text/plain, */*`, `content-type: application/json`, `origin: https://cdn.tgmrkt.io`, `referer: https://cdn.tgmrkt.io/`, `authorization: <token>`, `cookie: access_token=<token>` (:43-51). Сессия `curl_cffi` с `impersonate="chrome"`. 401, 403 и 404 трактуются как отказ в токене (:70-71).
- **`POST /gifts/saling`.** Тело (:87-112): `{"count": ≤20, "cursor": "", "collectionNames": [..], "modelNames": [..], "backdropNames": [..], "symbolNames": [], "minPrice": null, "maxPrice": null, "number": null, "isPremarket": false, "isNew": null, "luckyBuy": false, "giftType": null, "craftable": null, "isCrafted": null, "tgCanBeCraftedFrom": null, "removeSelfSales": true, "isTransferable": true, "availableForStaking": null, "forGame": null, "ordering": "Price", "lowToHigh": true, "query": null}`. Ответ: `{"gifts":[…]}` (:186).
- **`POST /feed`.** Тело (:115-129): `{"count": ≤20, "cursor": "", "collectionNames": [], "modelNames": [], "backdropNames": [], "number": null, "type": ["Sale","Listing","ChangePrice"], "minPrice": null, "maxPrice": null, "ordering": "Latest", "lowToHigh": false, "query": null}`. Ответ: `{"items":[{"id", "type", "amount", "date", "gift":{…}}]}` (:432-437; фикстура старого test_mrkt_watch.py:161-164). Курсорная пагинация не используется, `cursor` всегда `""`.
- **Поля gift** (фикстура `raw_gift`, test_mrkt_watch.py:9-28 в HEAD, такая же была в старой версии): `id, number, collectionName, modelName, backdropName, symbolName, salePrice, salePriceWithoutFee, isOnSale, isOnAuction, isMine, isLocked, isLockedForSale, premarketStatus, nextResaleDate`. Парсер читает ещё `collectionTitle`/`title`, `unlockDate`, `returnLockedUntil` (mrkt_watch.py:214-254).
- **Единицы:** `salePrice` и `amount` — **nanoTON** (целое, `/1e9`, `NANOTON`, mrkt_watch.py:31, 97-98). В фикстуре `salePrice = 10_000_000_000` (10 TON) и `salePriceWithoutFee = int(price/1.02)`. Значит, `salePrice` включает надбавку 2% сверх цены продавца. Отсюда `BUYER_MARKUP = 1.02` (mrkt_watch.py:32). Это вывод из фикстуры, а не из документации MRKT. `amount` события имеет приоритет над `salePrice` подарка (mrkt_watch.py:217-219).
- **Авторизация:** токен пользовательской сессии Mini App `@mrkt/app`. Как его получать (`/auth` с initData), в коде **не найдено**. Был временный workflow с SOCKS-прокси для входа (см. «Доверие»).
- **Swift Gifts (HEAD):**
  - `POST https://partners.swiftgifts.tg/api/actions/services/mrkt?page=0&limit=N`, тело `{"type": "listing"|"buy"|"change_price"}`, ответ `{"markets":[{"data":[…]} | row]}` (mrkt_watch.py:112-115, 520-549).
  - `POST /api/aggregator?page=0&limit=N`, тело `{"market":["mrkt"], "sort_by":"price asc", "fee":0, "collections":[..], "models":[..], "backdrops":[..]}`, ответ `{"items":[…], "meta":{"partial","providerErrors","providers_disabled"}, "has_more"}` (mrkt_watch.py:101-109, 257-276; bot.py:94-125). Если в meta есть `partial`, `providerErrors` или `providers_disabled`, это считается ошибкой.
  - Заголовок `x-api-key`. Поля строки: см. «Фикстуры».
- Deep link: `https://t.me/mrkt/app?startapp=feed<eventId без дефисов>` или `gift<id без дефисов>` (mrkt_watch.py:349-358).

### A8. Антидубли уведомлений и замена сообщения на «ПРОДАНО»

- **Антидубль на получателя:** таблицы `{tonnel|portals|mrkt}_alerts_by_chat(chat_id, id=gift_id, price, sent)`. Повторное сообщение уходит, **только если новая цена строго ниже** ранее отправленной (`if old and result["price"] >= old: return False`) (tonnel_watch.py:606-655; portals_watch.py:539-592; mrkt_watch.py:379-432). Есть миграция со старой таблицы без chat_id для владельца (:620-624). Проверено тестом: та же цена и 11 не отправляются, 9 отправляется (старый test_mrkt_watch.py, test_same_or_higher_price_is_not_sent_twice).
- **Антидубль событий:** `tonnel_events(id)` и `mrkt_events(id)` хранятся 8 суток. У Portals вместо них `portals_seen(id, price)` со сроком 8 суток (tonnel_watch.py:722-730, 784; mrkt_watch.py:439-444, 515; portals_watch.py:730). Активность дедуплицируется по `event_id` в `market_activity` (market_data.py:40-60); для Portals ключ `portals:<id>:<kind>:<price>` (portals_watch.py:699-701).
- **Запоминание сообщения:** `remember_alert()` пишет `offer_messages_by_chat(market, gift_id, chat_id, message_id, offer_price, gift_name, gift_num, model, sent, sold, checked, sold_at, preview_url)` и `signal_log` для дневного отчёта (alert_tracking.py:12-41, 52-88). `message_id` берётся из ответа `sendMessage` (bot.py:173-175).
- **«ПРОДАНО»:** `mark_offer_sold()` выбирает непроданные записи по `(market, gift_id)` и для каждого чата вызывает `editMessageText` (alert_tracking.py:153-204; bot.py:178-201).
  - Текст: `🔴 <b>ПРОДАНО</b>`, название `#номер`, площадка, модель, «Цена оффера», а «Цена продажи» добавляется, только если она отличается от цены оффера (alert_tracking.py:128-150).
  - Превью `t.me/nft/…` сохраняется, inline-кнопки снимаются (`reply_markup: {"inline_keyboard": []}`).
  - После редактирования в записях ставится `sold=1`, `sold_at`, и в историю Supabase уходит `{"action":"sold"}`.
  - Триггеры: Tonnel `sale.completed` (tonnel_watch.py:735-742); MRKT событие `Sale`/`buy` (mrkt_watch.py:459-467); Portals опрос `/nfts/{id}` со `status == "sold"` (`pending_offer_ids` каждые 30 с, партия по 2, alert_tracking.py:91-117; portals_watch.py:193-211).

### A9. Кэш флоров (TTL), SQLite-чекпоинты, history_store, Supabase

- **TTL кэшей** (config.json):

  | Что | TTL | Где хранится |
  |---|---|---|
  | Книга коллекции Tonnel | 900 с (15 мин, :57) | `tonnel_collection_books`, tonnel_watch.py:231-257 |
  | Книги модели и фона Tonnel | 1800 с (30 мин, :66) | `tonnel_variant_books`, :141-228 |
  | Книги Portals | 120 с (:35) | `portals_books`, portals_watch.py:290-331 |
  | Статистика коллекции Portals | 60 с | |
  | Соответствие имя → collection_id Portals | 24 ч | |
  | Книги MRKT | 20 с (:41) | `mrkt_books` |
  | Курс TON/RUB | 3600 с | `rates` |
  | Монохром | 30 дней, при ошибке 1 ч | `gift_special_traits` |

  При межплощадочном сравнении флор модели Tonnel берётся с TTL 20 с через `setdefault`, если в конфиге нет значения. В обычном конфиге значение есть, поэтому фактически действует 1800 с (portals_watch.py:393-404).
  - Бюджет прогрева: `variant_query_budget_per_cycle` = 2 и `…_per_event` = 2 (config.json:68-69). Ключи книг сверх бюджета в этом цикле не запрашиваются (tonnel_watch.py:194-196).
  - `cross_market_floor_cache_seconds` = 120 (:58) задан, но **в коде не используется** (grep не нашёл).
- **SQLite:** WAL, `busy_timeout` 30000 для state и 5000 для settings (tonnel_watch.py:957-963). Перед сетевыми запросами явно делается `commit`, чтобы не держать блокировку записи (tonnel_watch.py:743-744; portals_watch.py:703-704; коммит 8130015 «Prevent listener database lockups»).
- **checkpoint_sqlite.py:** для `state.sqlite3` и `settings.sqlite3` выполняет `PRAGMA wal_checkpoint(TRUNCATE)`. Если результат busy, бросает ошибку (:8, 11-20). Запускается в шаге `if: always()` перед `actions/cache/save` (gift-watch.yml:115-128). Каждый запуск Actions восстанавливает базы из кэша по префиксу ключа и удаляет старые кэши (:34-43, 130-140). Процессы живут `STREAM_SECONDS` = 3300 с, затем workflow ставит себя в очередь снова (cron `17 * * * *` плюс самозапуск, :5, 142-151).
- **history_store.py:**
  - Токен доступа чата = `HMAC-SHA256(history_writer_token, chat_id)` (:15-21).
  - Записи сначала попадают в очередь SQLite `history_outbox(chat_id, kind, event_key PK…)` и отправляются POST'ом на Edge Function с заголовком `x-writer-token`. При ошибке сети запись остаётся в очереди до следующего вызова (:24-31, 34-63, 90-139).
  - Типы записей: `offer` (`event_key = market:gift_id`), `upgrade`, `sold` (:142-196).
  - Синхронизация настроек: `settings_register` и `settings_sync`, опрос не чаще раза в 5 с (:70-87; runtime_settings.py:480-527).
- **Supabase:** таблицы `gift_watch_history` (уникальность по `chat_id, kind, event_key`, индекс по `access_hash`) и `gift_watch_settings`. RLS включён, права у `anon`/`authenticated` отозваны (supabase/schema.sql:1-46). Edge Function работает с `SUPABASE_SERVICE_ROLE_KEY` из env, CORS разрешён только для `https://topcvetok.github.io` (index.ts:1-4). В config.json и workflow указан URL проекта, это не секрет.

---

## Комиссии

Все цифры ниже взяты из кода и конфига. Тарифов маркетов код не знает, это «резервы».

| Параметр | Значение | Где | Что это |
|---|---|---|---|
| `tonnel_round_trip_cost_fraction` | 0.02 | config.json:77 | «Консервативный резерв на сборы и движение цены» (README.md:115). Это не тариф Tonnel |
| `portals_round_trip_cost_fraction` | 0.02 | config.json:38; portals_watch.py:523-528 | Аналогичный резерв |
| `mrkt_round_trip_cost_fraction` | 0.0196078431 = 1 − 1/1.02 | config.json:42; mrkt_watch.py:32, 312-317 | Выведено из `BUYER_MARKUP = 1.02` (надбавка покупателю в `salePrice`, фикстура `salePriceWithoutFee = price/1.02`) |
| `undercut_ton` | 0.01 TON | config.json:76 | Перепродажа чуть ниже флора |
| `fixed_cost_ton` | 0 | config.json:78 | Фиксированные расходы |
| `costs.{tonnel,mrkt}.sell_fee_fraction`, `extra_buy_rub`, `transfer_and_withdraw_rub` | `null` | config.json:79-92 | Используются только в старом режиме watchlist (bot.py:54-91). README.md:83-88 прямо говорит, что `null` означает «не ноль», а 0.02 — лишь пример |
| Swift `fee: 0` | 0 | mrkt_watch.py:102; bot.py:100 | Параметр запроса агрегатора |

Каждый резерв применяется к **перепродаже**: `net = resale·(1 − cost)`. Если в API Tonnel цена указана без комиссии покупки (в нашем задании C это 10%), код её **не учитывает**: цена покупки берётся «как есть» (tonnel_watch.py:277, 307). Подтверждений размера комиссии в коде нет. Выбор «где выгоднее перепродать» сравнивает `floor_модели·(1 − {market}_round_trip_cost_fraction)` по площадкам (alert_format.py:11-34).

## Фикстуры: структуры ответов маркетов (из тестов)

Все примеры ниже **из фикстур тестов**, не из живых ответов. Фикстуры автор писал сам и мог упростить.

- **Tonnel `pageGifts`, элемент списка** (test_tonnel_watch.py:10-24): `{"gift_id": int, "gift_num": int, "name": "Chill Flame", "price": 3.57, "asset": "TON", "status": "forsale", "auction": null|{}, "dutchAuctionData": null|{}, "premarketData": null|{}, "underLoan": false, "model": "Rare Model (1%)", "backdrop": "Black (1%)"}`. Пустой `{}` у `auction`, `dutchAuctionData` и `premarketData` означает обычный лот (:111-113).
- **События Tonnel (coffin.meme):**
  - `sale.completed`: `{"eventId":"sale-…", "type":"sale.completed", "occurredAt":ISO, "data":{"gift":{"gift_id","gift_num","gift_name","model":"Rare Model (1%)","backdrop":"Black (1%)","symbol":"Star (1%)"}, "price":7.0, "asset":"TON", "source":"FIXED"}}` (test_tonnel_watch.py:27-47).
  - `listing.created`: `data = {"gift":{…}, "price":5.5, "asset":"TON", "sale_type":"FIXED"}` (:507-527).
  - `listing.price_changed`: `data = {"gift":{…}, "previous_price":5.5, "price":5.0, "asset":"TON"}` (:529-544).
  - Встречаются также `sale_type: "DUTCH"` и тип `premarket.listing_created` (:546-558).
  - Ответ REST-догонки: `{"events":[…], "nextAfter":"<eventId>"}` (tonnel_watch.py:802-807, только код).
- **Portals `/api/nfts/search` → `{"results":[…]}`** (test_portals_watch.py:10-28, 67-76): `{"id":"p1", "tg_id":"EvilEye-42", "collection_id":"collection-evil-eye", "external_collection_number":42, "name":"Evil Eye", "price":"8", "status":"listed", "listed_at":ISO, "unlocks_at":"2025-01-01T00:00:00Z", "attributes":[{"type":"model","value":"Watcher"},{"type":"backdrop","value":"Onyx Black"},{"type":"symbol","value":"Moon"}]}`. `/api/nfts/{id}` — тот же объект с `status:"sold"` (:350-359). `/api/collections` → `{"collections":[{"id","name","sales_24h_count":5,…}]}` (:117; portals_watch.py:228-237).
- **MRKT `/api/v1/gifts/saling` → `{"gifts":[gift]}`, `/api/v1/feed` → `{"items":[{"id":"sale-1","type":"Sale"|"Listing"|"ChangePrice","amount":11000000000,"date":ISO,"gift":gift}]}`** (`git show b0e81f2^:test_mrkt_watch.py`, test_fetch_book_maps_api_response, test_sale_is_recorded_once). Структура gift: `{"id":"g1","number":42,"collectionName":"Evil Eye","modelName":"Watcher","backdropName":"Onyx Black","symbolName":"Moon","salePrice":10000000000,"salePriceWithoutFee":9803921568,"isOnSale":true,"isOnAuction":false,"isMine":false,"isLocked":false,"isLockedForSale":false,"premarketStatus":null,"nextResaleDate":null}` (test_mrkt_watch.py:9-28).
- **Swift Gifts (MRKT через партнёра):** `{"provider":"mrkt", "giftId":"g1", "seller_price_ton":10.0, "webapp_url":"https://t.me/mrkt/app?startapp=giftg1", "normalized":{"gift":{"id","collection","number","slug":"evileye-42","telegram_url","image_url","webapp_url","attributes":{"model":{"name"},"backdrop":{"name"},"symbol":{"name"}},"minted","on_sale","premarket"}, "price":{"currency":"TON","basis":"listing_ask","ton":10.0,"nano":"10000000000","total_ton","seller_ton"}, "market":{"provider":"mrkt","event_id","event_type":"listing"}}}` (test_mrkt_watch.py:31-59). Агрегатор: `{"items":[row], "meta":{}}` (:183-195).
- **Clue:** `{"score": 0..100}` (special_traits.py:50-54, только код).

---

## Что берём

| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Флор = минимум из остальных лотов при условии «N-й по цене не выше флора на X%». Отдельные N и X для коллекции (5 / 8%) и для модели и фона (3 / 20%), лот исключается из своей книги | `pricing/floor.py` | Переписать идею. Параметры вынести в конфиг пресета |
| Фильтр сигнала: скидка ≥15%, прибыль ≥100 ₽ и ROI ≥15% после резерва, `min_floor` ≥1000 ₽, `max_lot` | `rules/` | Идея, пороги как значения по умолчанию пресета |
| Подтверждение медианой реальных продаж за 24 ч (≥3 сделки по тому же основанию), `resale = min(флор, медиана)` | `pricing/sales.py` | Идея. Хранить продажи из всех потоков в одной таблице с `source` |
| Индекс ликвидности `sales·3 + listings + price_changes·2 + other` | `pricing/liquidity.py` | Идея, пороги 10 и 30 подобрать заново |
| Красивый номер `len(set(digits)) ≤ k` | `rules/traits.py` | Тривиально, переписать |
| Монохром через Clue (`/api/mono/resolve?url=slug` → `score`), кэш 30 дней, повтор через 1 ч | `pricing/traits.py` | Как внешний опциональный источник. Плюс своя реализация по картинке Fragment (идея из `classify_backdrop`) |
| Поток событий Tonnel (формат `eventId/type/occurredAt/data`, догонка по курсору `after` и `nextAfter`) | `markets/tonnel.py` | Формат API. Сначала проверить, что такое coffin.meme и можно ли ему доверять (см. «Открытые вопросы») |
| Portals: `portal-market.com/api`, `/nfts/search` (параметры), `/collections` (`sales_24h_count`), `/nfts/{id}` (`status: sold`), цена — строка в TON | `markets/portals.py`, `docs/MARKETS.md` | Формат API |
| MRKT: тела `/gifts/saling` и `/feed`, nanoTON, `salePriceWithoutFee` | `markets/mrkt.py`, `docs/MARKETS.md` | Формат API, сверить с заданием D |
| Антидубль «повторять только при снижении цены» по каждому чату, дедуп событий по id с TTL 8 суток | `bot/notify.py` | Идея |
| Правка отправленного сообщения в «ПРОДАНО» (`editMessageText`, снять кнопки, оставить превью) и триггеры по маркетам | `bot/` | Идея |
| Ограничитель частоты на клиента (1,2 с, 1,05 с), 429 → `Retry-After` с нижним и верхним пределом, прерывание цикла на первом 429 | `markets/base.py` | Идея |
| `commit` перед сетевыми вызовами, WAL, `busy_timeout` | `storage/` | Идея |
| Очередь outbox для внешней доставки | `storage/outbox.py` | Идея (на будущее) |

## Что НЕ берём и почему

- **Код целиком:** лицензии нет.
- **GitHub Actions как постоянный сервер** с самозапуском и состоянием в кэше Actions: хрупко, похоже на злоупотребление бесплатным CI. У нас будет VPS или systemd.
- **Временный SOCKS-прокси через pinggy** (удалённый workflow): небезопасно и противоречит нашим правилам.
- **Партнёрский API Swift Gifts:** нужен платный или выданный по договорённости ключ, это посредник. Можно держать как резервный источник, но не как основной.
- **Резерв 2% вместо реальных комиссий** и игнор возможной комиссии покупки Tonnel: у нас комиссии должны быть точными и проверенными.
- **Многопользовательский режим, Mini App, Supabase:** не MVP.
- **Монитор улучшений через перебор HEAD-запросов к Fragment и парсинг HTML t.me:** не про флип. Идея на потом (задание H).

## Открытые вопросы

1. Кто владеет `gifts.coffin.meme` и официальный ли это поток Tonnel? Есть ли у самого Tonnel WebSocket? В этом коде не найдено. Сверить с заданиями C и E (tonnelmp, boostNT/Tonnel-API).
2. Входит ли комиссия покупки Tonnel в `price` из `pageGifts` и из событий? Код считает, что цена «как есть».
3. MRKT: `salePrice` = цена продавца ×1.02? Это видно только из фикстуры автора. Проверить на живом ответе вместе с заданием D.
4. Почему автор ушёл с прямого MRKT API? В коммите сказано лишь, что «официальный API MRKT выдаёт токен только пользовательской Telegram-сессии» (diff README в b0e81f2). Работает ли `/feed` с обычным токеном из `/auth`, проверить в задании D.
5. Portals: какие ещё поля есть в `/collections` (кроме `id`, `name`, `sales_24h_count`), например флор? Код другие поля не читает. Отдаёт ли `/nfts/search` 429 без токена при опросе раз в 5 с?
6. Clue: лимиты и условия использования `app.clue.tg/api/mono/resolve`. В коде не найдено.

## Для MARKETS.md

**Tonnel**
- Каталог: `POST https://gifts2.tonnel.network/api/pageGifts`. Тело `{"page":1,"limit":N,"sort":"<JSON-строка>","filter":"<JSON-строка>","price_range":null,"user_auth":""}`. Фильтр активных TON-лотов: `{"price":{"$exists":true},"refunded":{"$ne":true},"buyer":{"$exists":false},"export_at":{"$exists":true},"gift_name":…,"asset":"TON"}` плюс `model`/`backdrop`. Ответ — JSON-массив. [код tonnel_watch.py:117-138]
- Заголовки: `origin: https://market.tonnel.network`, `referer: https://market.tonnel.network/`, `accept: */*`, `accept-language: ru-RU,…`, `content-type: application/json`. Отпечаток через `curl_cffi impersonate="chrome"`, cookies нет. Без имитации отвечает 403. [код tonnel_watch.py:32-38, 93-96; README.md:32, 61]
- Атрибуты приходят с суффиксом редкости: `"Black (1%)"`. Активный лот определяется так: `status=="forsale"`, `asset=="TON"`, нет `auction`/`dutchAuctionData`/`premarketData`, `underLoan is False`. [код tonnel_watch.py:68, 260-271]
- Поток событий (сторонний домен): `wss://gifts.coffin.meme/api/marketplace/ws`, кадры — JSON-события без подписки. Догонка: `GET https://gifts.coffin.meme/api/marketplace/events?after=<eventId>&limit=100` → `{"events":[…],"nextAfter":…}`. Типы: `listing.created` (`data.sale_type` FIXED/DUTCH), `listing.price_changed` (`data.previous_price`), `sale.completed`, `premarket.listing_created`. Цена в TON (число). [код tonnel_watch.py:29-30, 658-705, 789-852; фикстуры test_tonnel_watch.py]
- Ссылка на лот: `https://t.me/tonnel_network_bot/gift?startapp=<gift_id>`. [код :590-591]
- 429 → `retry-after`. [код :100-105]

**Portals**
- Base URL: `https://portal-market.com/api` (без «s»), `origin`/`referer` `https://portal-market.com`. [код portals_watch.py:45, 57-66]
- `GET /nfts/search?offset=0&limit≤20&sort_by=price asc|listed_at desc&status=listed&collection_ids=<uuid>|filter_by_collections=<name>&filter_by_models=…&filter_by_backdrops=…` → `{"results":[{id, tg_id, collection_id, external_collection_number, name, price:"строка TON", status, listed_at, unlocks_at, attributes:[{type,value}]}]}`. Работает без авторизации. [код :155-183; фикстура test_portals_watch.py:10-28, 67-76; README.md:34]
- `GET /collections?search=<name>&limit=10` → `{"collections":[{id,name,sales_24h_count,…}]}`. [код :214-287]
- `GET /nfts/{id}` → объект с `status` (`listed`/`sold`) и `price`. [код :186-211]
- Клиент `curl_cffi impersonate chrome`, HTTP/1.1, `accept-encoding: identity`. Не чаще 1 запроса в 1,2 с, опрос раз в 5 с, 429 → `retry-after` (по умолчанию 30). [код :47, 69-101, 749-754; config.json:33]
- Deep link: `https://t.me/portals/market?startapp=gift_<id>`. [код :531-532]

**MRKT (прямой API, версия до b0e81f2)**
- Base `https://api.tgmrkt.io/api/v1`. Заголовки `origin`/`referer` `https://cdn.tgmrkt.io/`, `authorization: <token>`, `cookie: access_token=<token>`. Токен пользовательской сессии. [код `git show b0e81f2^:mrkt_watch.py`:27, 43-51]
- `POST /gifts/saling`, тело `{count≤20, cursor:"", collectionNames, modelNames, backdropNames, symbolNames, minPrice, maxPrice, number, isPremarket:false, isNew, luckyBuy:false, giftType, craftable, isCrafted, tgCanBeCraftedFrom, removeSelfSales:true, isTransferable:true, availableForStaking, forGame, ordering:"Price", lowToHigh:true, query}` → `{"gifts":[…]}`. [там же :87-112, 181-189]
- `POST /feed`, тело `{count≤20, cursor:"", collectionNames:[], modelNames:[], backdropNames:[], number:null, type:["Sale","Listing","ChangePrice"], minPrice, maxPrice, ordering:"Latest", lowToHigh:false, query}` → `{"items":[{id,type,amount,date,gift}]}`. [там же :115-129, 432-437]
- Цены `salePrice` и `amount` в **nanoTON**. В фикстуре `salePriceWithoutFee = salePrice/1.02`, то есть вероятная надбавка покупателю 2% (из фикстуры, не подтверждено). Поля gift: `id, number, collectionName, modelName, backdropName, symbolName, salePrice, salePriceWithoutFee, isOnSale, isOnAuction, isMine, isLocked, isLockedForSale, premarketStatus, nextResaleDate`. [код mrkt_watch.py:31-32, 97-98, 214-254; фикстура test_mrkt_watch.py:9-28]
- Deep link: `https://t.me/mrkt/app?startapp=gift<id без '-'>` / `feed<eventId без '-'>`. [код mrkt_watch.py:349-358]

**Swift Gifts (партнёрский агрегатор, сейчас источник MRKT в этом проекте)**
- `https://partners.swiftgifts.tg`, заголовок `x-api-key`. `POST /api/actions/services/mrkt?page=0&limit=N`, тело `{"type":"listing"|"buy"|"change_price"}` → `{"markets":[…]}`. `POST /api/aggregator?page=0&limit≤200`, тело `{"market":["mrkt"|"tonnel"],"sort_by":"price asc","fee":0,"collections","models","backdrops"}` → `{"items","meta":{partial,providerErrors,providers_disabled},"has_more"}`. 401/403 — нет доступа, 402 — ключ неактивен. [код mrkt_watch.py:30-115, 257-276, 520-549; bot.py:94-125]

**Прочее**
- Clue, монохром: `GET https://app.clue.tg/api/mono/resolve?url=<slug вида evileye-42>` → `{"score":0..100}`. [код special_traits.py:12, 39-54]
- Картинка подарка: `https://nft.fragment.com/gift/<slug>-<n>.small.jpg` (для несуществующего номера 404, иногда 500 для существующего). Атрибуты и владелец берутся из `<meta name="twitter:description">` и таблицы `Owner` на `https://t.me/nft/<Slug>-<n>`. [код upgrade_watch.py:32-33, 78-98, 150-198]
- Курс: CoinGecko `GET /api/v3/simple/price?ids=the-open-network&vs_currencies=rub`. [код tonnel_watch.py:31, 861-866]
