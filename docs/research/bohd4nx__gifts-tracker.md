# bohd4nx/gifts-tracker

> Источник: исходники, клон от 2026-11-09, коммит `a243c216d6e6368a21bfe57d3f9ddac33d3eb489`. Живых запросов к Telegram не было, код не запускался. Из старой версии отчёта ничего не перенесено: в ней не было фактов о коде.

- Ссылка: https://github.com/bohd4nx/gifts-tracker. В README бейджи и `git clone` ведут на `bohd4nx/GiftsTracker` (README.md:5-6, 34), то есть репозиторий, видимо, переименован или имеет второе имя.
- Язык / стек: Python ≥3.12 (pyproject.toml:5). Userbot на **kurigram** (форк Pyrogram, ветка `dev` из git, без фиксированной версии: pyproject.toml:8) + `tgcrypto-pyrofork==1.2.8`. Bot API для заливки стикеров через **aiogram ≥3.25** (pyproject.toml:10). БД PostgreSQL 17 через async SQLAlchemy 2 + psycopg 3 (pyproject.toml:12-14, docker-compose.yml:3). Docker/compose.
- Слой MTProto: в коде не найден. Он определяется веткой `dev` kurigram на момент установки и в репозитории не зафиксирован.
- Лицензия: **нет**. Файла LICENSE нет ни в текущем дереве, ни в истории (`git log --all -- 'LICENSE*'` пусто). В README и pyproject лицензия не указана (pyproject.toml:1-15 содержит только name/version/description/authors). Значит, все права у автора, и код копировать нельзя (AGENTS.md §4.4).
- Последний коммит / активность: 2026-08-13 (`a243c21`, «clean up code… notification footer emojis»). Первый коммит 2026-02-08. Активная разработка шла с февраля по май 2026, потом точечные правки.
- Звёзды / форки / коммиты: звёзды и форки не установлены. Коммитов **38**: клон не shallow (`git rev-parse --is-shallow-repository` = false), это полная история. 3 PR от самого автора.
- Доверие: **среднее**. Код читаемый, малвари нет (см. «Признаки риска»). Минусы: нет лицензии, клиент маскируется под Telegram Desktop со встроенными по умолчанию публичными API_ID/API_HASH, в уведомлениях реферальная ссылка автора.

## Что делает (2–3 предложения)

Userbot (пользовательский аккаунт Telegram) раз в `INTERVAL` секунд вызывает `payments.getStarGifts` с кэширующим `hash`. Ответ сравнивается с таблицей `gifts` в PostgreSQL, и бот публикует в канал уведомления трёх видов: «новый подарок в магазине», «открыто улучшение / изменилась цена улучшения», «доступен крафт: +N моделей». Попутно он заливает стикер подарка в отдельный канал (через Bot API) для красивого link preview и добавляет подарок в собственный пак кастомных эмодзи. Ничего не покупает и не работает с маркетами.

## Как устроено

### Источник данных и частота опроса
- Только MTProto, polling. Цикл `while True` → `process_gifts` → `asyncio.sleep(config.INTERVAL)` (app/services/monitor.py:25-38).
- `INTERVAL` по умолчанию **15.0 с** (app/core/config.py:35; README.md:69; .env.example:20). После ошибки тоже ждёт `INTERVAL` (monitor.py:42-44). При `FloodWait` спит `e.value` секунд (monitor.py:39-41).
- Клиент создаётся с `sleep_threshold=30`: kurigram сам «проглатывает» FloodWait до 30 с (main.py:39). Также `skip_updates=True`, `workers=8` (main.py:37-38).
- Других эндпоинтов (маркеты, HTTP API) нет. Все ссылки в коде ведут только на t.me (grep `http` по *.py).

### MTProto-методы и параметры (всё из кода)
| Метод | Где | Параметры / как используется |
|---|---|---|
| `payments.getStarGifts` | app/services/gifts/fetch.py:15 | `hash=last_hash`. Если ответ `payments.StarGiftsNotModified`, список не изменился и цикл ничего не делает (fetch.py:17-19). Иначе берёт `result.gifts` и сохраняет `result.hash` для следующего вызова (fetch.py:21-22). |
| `payments.getStarGifts` | app/services/emoji/build.py:18-20 | `hash=0`, один раз при создании эмодзи-пака: берёт все подарки со стикером `application/x-tgsticker` и сортирует по `last_sale_date`. |
| `app.get_gift_upgrade_variants(gift_id)` | app/services/crafts/notification.py:22 | Высокоуровневый метод kurigram, берётся `len(variants.models)`. Какой raw-метод MTProto под ним, в клоне не найдено (исходников kurigram в репо нет). |
| `stickers.createStickerSet` | app/services/emoji/sticker_set.py:40-48 | `emojis=True`, первый стикер; дальше пауза 2 с. |
| `stickers.addStickerToSet` | sticker_set.py:62-67 | Добавляет стикер подарка в пак, затем пауза 1.5 с (add.py:21, build.py:52). |
| `messages.getStickerSet` | sticker_set.py:71-76 | `hash=0`, проверка существования пака при старте (emoji/init.py:16-24). |
| `Ping` | app/commands/status.py:19 | Для команды `.status`. |
| `send_message` / `edit_message_text` / `get_chat` / `download_media` | notifications/base.py:19, 41; utils/display.py:52; gifts/upload.py:20 | Высокоуровневые вызовы Pyrogram. |

Про кэширование `hash`:
- `last_hash` хранится **только в памяти** и стартует с 0 (monitor.py:21). После каждого рестарта первый цикл получает полный список. Он не считает старые подарки новыми, потому что сравнение идёт с БД (см. ниже).
- В первом коммите `a897bf3` вызывался `GetStarGifts(hash=0)` на каждом цикле (`git show a897bf3:app/methods/fetch_gifts.py`). Кэширующий `hash` появился в `10141ab` (2026-03-17).
- Важное следствие: пока Telegram отвечает `NotModified`, детекторы улучшений и крафтов не запускаются. Вся логика держится на том, что сервер меняет `hash` при любом изменении полей подарка. Это допущение автора, в коде оно не проверяется.

### Как определяются события (всё из кода)
Сравнение «текущий ответ ↔ история из БД» (app/services/processor.py:21-74). История каждый цикл заново читается из таблицы `gifts` (monitor.py:30-32).

1. **Новый подарок**: `new_ids = current_gifts.keys() - gifts_history.keys()` по `StarGift.id` (processor.py:28). Для каждого нового подарка параллельно выполняются заливка стикера в канал стикеров (Bot API `send_sticker`, gifts/upload.py:29-31) и добавление в эмодзи-пак (new_gifts.py:25-28). Затем пауза 3 с, «чтобы Telegram проиндексировал пост для link preview» (new_gifts.py:36-37), уведомление в канал и пауза 1 с между подарками (new_gifts.py:49-50).
2. **Открыто улучшение**: `old.upgrade_price is None and new.upgrade_price > 0` (app/services/upgrades/detector.py:4-7). `upgrade_price` = `StarGift.upgrade_stars` (utils/parser.py:17). Отправляется отдельное сообщение, его id сохраняется в `upgrade_msg_id` (upgrades/notification.py:21-22).
3. **Изменилась цена улучшения**: оба значения не None, они различаются, и уже есть `upgrade_msg_id` (detector.py:10-13). Новое сообщение не отправляется: **редактируется** прежнее сообщение об улучшении (upgrades/notification.py:28-37).
4. **Крафт**: `raw.upgrade_variants` вырос (app/services/crafts/detector.py:4-9). `upgrade_variants` берётся как атрибут `StarGift` через `getattr` (parser.py:32). Затем вызывается `get_gift_upgrade_variants`, считается `len(models)` и сравнивается с сохранённым `raw.models_count`. Уведомление уходит только при `delta > 0` (crafts/notification.py:22-31).
   - Замечание из кода: при первом крафте `models_count` = None → 0, поэтому `delta` равна полному числу моделей, а не приросту (notification.py:24-25). Сам детектор считает разницу по `upgrade_variants`, но в текст попадает `delta` по моделям.
5. Порядок проверок `if/elif`: за один цикл по одному подарку срабатывает не больше одного события (processor.py:64-74).
6. Исчезновение подарка из магазина (sold out / снят) **не отслеживается**: сравнивается только `current - history`, удалённые не обрабатываются (в коде не найдено).
7. Изменения `availability_remains` (остаток) не отслеживаются: поле даже не парсится (parser.py:14-35).

### Модель данных подарка (что парсится из `StarGift`, utils/parser.py:11-35)
`id`, `stars` → `price`, `upgrade_stars` → `upgrade_price`, `availability_total` → `total_amount`, стикер (`dc_id, id, access_hash, file_reference` → закодированный `file_id`), а также в `raw`: `title`, `require_premium`, `limited_per_user`, `per_user_total`, `locked_until_date`, `released_by` (класс пира + `channel_id`/`user_id`), `auction`, `auction_slug`, `gifts_per_round`, `upgrade_variants`, `models_count`.

### Схема БД (SQLAlchemy, app/database/models/gifts.py:9-35)
Одна таблица `gifts`, создаётся через `Base.metadata.create_all` без миграций (app/database/base.py:24-26):

| Поле | Тип | Смысл |
|---|---|---|
| `id` | BigInteger PK | `StarGift.id` |
| `price` | Integer NOT NULL | цена в звёздах |
| `upgrade_price` | Integer NULL | цена улучшения в звёздах |
| `total_amount` | Integer NULL | тираж (`availability_total`) |
| `sticker_file_id` | String(255) | Pyrogram file_id стикера |
| `sticker_raw` | Text | JSON: dc_id/id/access_hash/file_reference (bytes сериализуются через `repr`) |
| `sticker_msg_id` | Integer | id поста со стикером в канале стикеров |
| `msg_id` | Integer, индекс | id уведомления «новый подарок» |
| `upgrade_msg_id` | Integer, индекс | id уведомления об улучшении (для редактирования) |
| `emoji_id` | BigInteger | id документа в эмодзи-паке |
| `raw_data` | Text | JSON с полями из `raw` (см. выше) |
| `first_seen` | timestamptz, default now() | |
| `last_updated` | timestamptz, onupdate now(), индекс | |

Запись делается upsert `INSERT … ON CONFLICT (id) DO UPDATE` всей пачкой, только если в цикле были изменения (crud/gifts.py:47-74, monitor.py:35-36). JSON лежит в Text, а не в JSONB. bytes кодируются как `repr` и раскодируются через `ast.literal_eval` (app/utils/codec.py:12-37). Это безопасно: `literal_eval` не исполняет код.

### Формат уведомлений (HTML, пользовательский аккаунт шлёт в `CHANNEL_ID`)
Отправляет **userbot**, а не бот (notifications/base.py:19-23): без Premium-аккаунта кастомные эмодзи `<emoji id=…>` не отрисуются. Бот (aiogram) только заливает `.tgs` в канал стикеров.

Новый подарок (app/services/notifications/gifts.py:9-41), по строкам:
- `{эмодзи подарка} <b>New gift available</b>`
- `ID: <code>{id}</code>`
- `Released by: @{username}`, если есть `released_by`. Пир считается каналом: `-100{peer_id}` → `get_chat` (utils/display.py:47-53).
- `Price: <code>{price}</code>⭐ • Supply: <code>{total}</code>` (числа с точкой как разделителем тысяч, codec.py:6-9)
- для аукциона: `{total // gifts_per_round} rounds • {gifts_per_round} per round`
- ограничения: `Premium Only`, `{per_user_total} per user`, `Time Locked` (если `locked_until_date`)
- футер со ссылками на Tonnel (**реферальная ссылка автора**) и @RemovedGiftsBot (app/core/constants.py:22-28)

Link preview (utils/display.py:15-33): для аукциона `https://t.me/auction/{auction_slug}`, иначе пост со стикером `https://t.me/{STICKERS_CHANNEL_USERNAME}/{sticker_msg_id}`. В обоих случаях `prefer_small_media=True, show_above_text=True`.

Улучшение (notifications/upgrades.py:9-22): `Gift upgrade available`, ID, Released by, `Upgrade Price: <code>{n}</code> ⭐`. При смене цены то же сообщение редактируется.

Крафт (notifications/crafts.py:9-19): `Gift craft available • {delta} models`, ID, Released by.

Повтор отправки при FloodWait рекурсивный и без ограничения числа попыток (notifications/base.py:25-28, 48-51).

### Авторизация и хранение сессии
- Обычный Pyrogram/kurigram userbot по номеру телефона. `PHONE_NUMBER` и `PASSWORD` (2FA) берутся из env (config.py:23-24). Первый вход интерактивный: `docker compose run --rm app` (README.md:41-42).
- Сессия: файл `session/GiftsTracker.session` (это SQLite-файл Pyrogram) рядом с `main.py`: `name="GiftsTracker"`, `workdir=…/session` (main.py:22, 32). Каталог в `.gitignore` (.gitignore:15-18). В compose весь репозиторий смонтирован как том `.:/app` (docker-compose.yml:20-21), поэтому сессия лежит на хосте в каталоге проекта. Права на файл код не выставляет (в коде не найдено).
- Ошибки `AuthKeyUnregistered/AuthKeyDuplicated/SessionRevoked` только логируются с выходом из программы (main.py:63-64).
- Маскировка под официальный клиент: `device_model="PC 64bit"`, `system_version="Windows 10"`, `app_version="6.8.2 x64"`, `lang_pack="tdesktop"`, `client_platform=DESKTOP` (main.py:27-33). Если `API_ID/API_HASH` не заданы, по умолчанию подставляются `2040` и **захардкоженный API_HASH** (config.py:21-22). Судя по README («API_ID default 2040»), это публичная пара Telegram Desktop; значение хэша в отчёт не переносим. Использовать чужой api_id запрещено правилами Telegram API и повышает риск бана аккаунта.

### Предохранители и лимиты
- Паузы: 15 с между циклами, 3 с перед уведомлением о новом подарке, 1 с между новыми подарками, 1.5–2 с между операциями со стикер-паком.
- FloodWait: обработан на уровне цикла, отправки сообщений и эмодзи-пака. Плюс `sleep_threshold=30`.
- Денег не касается: нет покупок, нет баланса звёзд (`payments.getStarsStatus` и т.п. в коде не найдено).

### UI
Единственная команда: `.status` / `status` / `/status`, работает только от своего аккаунта (`filters.me`). Она редактирует сообщение и показывает DC, ping, `INTERVAL` и число подарков в БД (app/commands/base.py:8-20, status.py:14-33).

### Хранение состояния
PostgreSQL (таблица `gifts`), `last_hash` в памяти, `pack_ref` эмодзи-пака в памяти модуля (app/services/emoji/state.py:4).

## Признаки риска
- Малварь: **не обнаружено**. Нет `exec`/`eval`/base64, нет обфускации, нет сетевых вызовов кроме Telegram (MTProto + Bot API через aiogram). Сессия никуда не отправляется. Бинарников в репо нет. В истории не было закоммиченных `.env`/`*.session` (проверено по `git log --all --name-only`, только `.env.example` и `config.ini.example`).
- Захардкоженный дефолтный API_HASH (config.py:22) и подделка device/app_version под TDesktop (main.py:27-33). Это риск для аккаунта и нарушение правил Telegram API, но не малварь.
- Зависимость от плавающей ветки `kurigram@dev` из git (pyproject.toml:8): установка невоспроизводима, и при каждой сборке тянется непроверенный код.
- Реферальная ссылка автора на Tonnel в каждом уведомлении (constants.py:24).
- Нет лицензии, копировать код нельзя.

## Связь с gifts-buyer

Упоминаний `gifts-buyer`/`GiftsBuyer`, `GIFT_RANGES`, контроля баланса звёзд и логики покупки в gifts-tracker **нет** (grep по `buyer|GIFT_RANGES|balance|getStarsStatus` пуст). Общего кода (общего пакета или подмодуля) нет. Пересекается только то, что видно из этого репозитория:
- **Источник данных магазина тот же, что заявлен для gifts-buyer в задании G: `payments.getStarGifts`.** Здесь он вызывается с кэширующим `hash` и обработкой `payments.StarGiftsNotModified` (gifts/fetch.py:15-22). Если gifts-buyer у того же автора устроен похоже, «новые подарки» там тоже определяются как разность множеств `StarGift.id` между вызовами. Это **предположение**, по коду gifts-buyer не проверено.
- Поля `StarGift`, которые автор считает значимыми и которые нужны для правил покупки: `stars` (цена), `availability_total` (тираж, по нему обычно судят о редкости), `require_premium`, `limited_per_user`/`per_user_total`, `locked_until_date`, `upgrade_stars`, `auction`/`gifts_per_round`, `released_by` (parser.py:14-35). Поле `availability_remains` здесь не используется.
- Тот же стек автора: kurigram/Pyrogram userbot, вход по номеру телефона, `.env`.
- Наблюдение для повторной попытки задания G: README этого репо ссылается на `bohd4nx/GiftsTracker` (CamelCase), а не на `gifts-tracker`. Возможно, gifts-buyer тоже доступен под другим именем, например `bohd4nx/GiftsBuyer`. **Не проверялось**, сеть по заданию не использовалась.

## Что берём
| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Опрос `payments.getStarGifts(hash=…)` с кэшем по `hash` и ранним выходом на `StarGiftsNotModified` | (позже) модуль «новые подарки магазина», Telethon `functions.payments.GetStarGiftsRequest(hash=...)` | идея + формат API, переписать |
| Детекция «новый подарок» = разность множеств `id` с персистентной историей (а не с прошлым ответом в памяти), чтобы рестарт не давал ложных «новых» | там же | идея |
| Детекция «открыто улучшение» = `upgrade_stars` перешло из None в >0; «изменилась цена» = редактирование уже отправленного пуша | там же + `bot/` | идея (вместе с SOLD-обновлением из topcvetok, это один и тот же приём «храним msg_id и редактируем») |
| Детекция крафта по росту `upgrade_variants` и числу моделей | там же | идея, но поле и метод проверить по схеме слоя Telethon |
| Хранить `msg_id`/`upgrade_msg_id` в строке объекта для последующего редактирования | `bot/`, БД уведомлений | идея |
| Состав полей уведомления о новом подарке (цена, тираж, Premium-only, лимит на пользователя, time lock, аукцион: раунды) | `bot/` шаблоны | идея |

## Что НЕ берём и почему
- Код целиком и фрагменты: нет лицензии.
- Kurigram/Pyrogram: у нас Telethon (DECISIONS.md D-005).
- Эмодзи-пак, канал стикеров, link preview через пост: косметика для публичного канала, к флипу не относится.
- Захардкоженный API_ID/API_HASH и маскировка под TDesktop: риск для аккаунта владельца.
- Отправка уведомлений от userbot: у нас пуши шлёт бот.
- Бесконечный рекурсивный ретрай на FloodWait.

## Открытые вопросы
- Какой raw-метод стоит за `get_gift_upgrade_variants` в kurigram, и есть ли поле `upgrade_variants` у `StarGift` в слое нашей версии Telethon? Проверить по TL-схеме на Этапе 2.
- Действительно ли Telegram меняет `hash` у `payments.getStarGifts` при изменении только `upgrade_stars`/`upgrade_variants`? Автор на это полагается, у нас не проверено.
- Допустимая частота опроса `getStarGifts`: 15 с у автора работает без жалоб в коде, но официального лимита нет. Принять как ориентир «не чаще 15 с».

## Для MARKETS.md
Маркетов в репо нет. Факты для раздела «Telegram MTProto / магазин подарков»:
- `payments.getStarGifts(hash:int)`: при `hash` = прошлому `result.hash` возвращает `payments.StarGiftsNotModified`, иначе `payments.StarGifts{hash, gifts[]}`. Из кода (app/services/gifts/fetch.py:15-22).
- Поля `StarGift`, которые читаются: `id`, `stars`, `upgrade_stars`, `availability_total`, `sticker{dc_id,id,access_hash,file_reference,mime_type}`, `title`, `require_premium`, `limited_per_user`, `per_user_total`, `locked_until_date`, `released_by(Peer)`, `auction`, `auction_slug`, `gifts_per_round`, `upgrade_variants`, `last_sale_date`. Из кода (app/utils/parser.py:11-35, app/services/emoji/build.py:22-30).
- Единицы: цены в звёздах (целые). Из кода (notifications/gifts.py:20, upgrades.py:18-19).
- Частота опроса у автора: 15 с по умолчанию, FloodWait ≤30 с глотается клиентом. Из кода (config.py:35, main.py:39) и README:69.
- Ссылка на аукцион подарка: `https://t.me/auction/{auction_slug}`. Из кода (utils/display.py:19-21).
- Модели для крафта: высокоуровневый `get_gift_upgrade_variants(gift_id).models` (kurigram). Raw-метод в коде не найден (crafts/notification.py:22).
