# maxktz/telegram-gifts-radar

> Источник: исходники, клон от 2026-11-09, коммит `1ec0fc7259dea3d55a0d4d7b1fe8b024a835411a`. Клон полный, не неглубокий (`git rev-parse --is-shallow-repository` → `false`). Прочитаны все текстовые файлы: `src/*.ts`, `prisma/schema.prisma`, три миграции, `package.json`, `Dockerfile`, `docker-compose.yml`, `scripts/*.sh`, `.env.example`, `README.md`, `LICENSE`. `bun.lockb` и `assets/image.jpg` не открывались, это бинарные файлы. Ничего не запускалось.

- Ссылка: https://github.com/maxktz/telegram-gifts-radar
- Язык / стек: TypeScript, рантайм Bun (образ `oven/bun:1.1.42`, Dockerfile:3), GramJS (npm-пакет `telegram` `^2.26.16`, package.json:26), Prisma `^6.2.1` + PostgreSQL (package.json:16,22; schema.prisma:6), Joi, dotenv, `@inquirer/prompts`, Twilio `^5.4.2`. Точную версию GramJS из lock-файла не смотрел: он бинарный.
- Лицензия: MIT, «Copyright (c) 2025 Max Katz (@maxktz)» (LICENSE:1-3).
- Последний коммит / активность: `1ec0fc7` «update editing», 2025-01-27 07:53:14 +0200. Первый коммит `5c45754` «initial» сделан 2025-01-09. Вся разработка уложилась в 18 дней (9–27 января 2025). На 2026-11-09 проект без изменений почти 2 года.
- Звёзды / форки / коммиты: звёзды и форки не установлены, api.github.com закрыт. Коммитов 25, клон полный.
- Доверие: среднее/высокое как к справочнику. Код маленький (~400 строк), читается целиком. Обфускации, base64/eval, скачивания бинарников и отправки сессии на сторонние адреса нет. Внешние адреса только Telegram (GramJS) и Twilio, причём Twilio опционален. Код сырой, есть несколько явных багов (см. ниже), поэтому на детали алгоритма не опираемся.

## Что делает
Telegram-юзербот на личной сессии. Раз в N секунд запрашивает каталог подарков магазина через MTProto `payments.getStarGifts`. Для каждого подарка постит в каждый чат из `CHAT_IDS` два сообщения: стикер и текст с ценой и остатком. Потом периодически редактирует текстовое сообщение, когда меняется остаток, и ставит хэштег `#soldout`/`#instock`. Когда появляется новый подарок, звонит выбранным людям: Telegram-звонком через `phone.requestCall`, а если не ответили, обычным телефонным звонком через Twilio. Апгрейды (улучшения) подарков, NFT и маркеты проект не отслеживает.

## Как устроено

### Источник данных
- Метод: только `payments.getStarGifts` с `hash: 0`, из кода (src/gifts-radar.ts:22-24):
  ```ts
  const giftsResult: Api.payments.StarGifts = await this.client.invoke(
    new Api.payments.GetStarGifts({ hash: 0 }),
  )
  ```
  `hash` всегда 0, поэтому сервер каждый раз отдаёт полный список. Механизм `StarGiftsNotModified` не используется, и его обработки в коде нет.
- Другие MTProto-методы в коде: `messages.getDhConfig` (notifications-service.ts:117-121), `phone.requestCall` (:43-57), `phone.discardCall` (:66-76). Кроме них используются высокоуровневые вызовы GramJS: `sendMessage`, `editMessage`, `deleteMessages`, `downloadMedia`, `uploadFile`. Методы для апгрейдов и уникальных подарков (`getStarGiftUpgradePreview`, `getUniqueStarGift` и т.п.) в коде не найдены.
- Сортировка: по `gift.id` по возрастанию, с комментарием «sort by date asc» (gifts-radar.ts:26-28).
- Частота опроса: по умолчанию **10 секунд**, это `updateIntervalSec: number = 10` в конструкторе (gifts-radar.ts:13). `main.ts:84-89` создаёт `GiftsRadar` без этого аргумента, значит работает 10 с. Пауза отсчитывается после завершения всей итерации: `await sleep(this.updateIntervalSec * 1000)` (gifts-radar.ts:56). Реальный период = 10 с + время обработки.
- История константы по git: 30 (`5c45754`, initial) → 50 (`f7d4a5b`) → 40 (`2acc7cc`) → 10 (`e7cadf0`) → 15 (`da3699b`) → 10 (`1ec0fc7`, последний коммит).
- Редактирование уже отправленных уведомлений идёт не на каждой итерации, а на каждой 5-й: `const editExisting = i % 5 === 0` (gifts-radar.ts:41). Это примерно раз в 50 с с лишним.
- README:13 пишет «Monitors Telegram gifts every 30 seconds». Это устарело, 30 было только в первом коммите.

### Как определяют новые подарки
- Из кода (gifts-radar.ts:30-37): из таблицы `StarGift` читаются все `giftId`, кладутся в `Set`, и подарок считается новым, если его `id` в этом множестве нет. Если хоть один подарок новый, запускаются звонки `sendCallNotifications()` (:47-49).
- Пост в чат решается отдельно для каждой пары «подарок × чат» (gifts-radar.ts:66-72): `findUnique` по составному ключу `(giftId, chatId)` в `StarGiftNotification`. Если записи нет, отправляется новое уведомление и делается upsert, а строка `StarGift` создаётся через `connectOrCreate` (:79-106).
- Следствия, выведенные из кода:
  - При пустой БД на первом запуске все подарки каталога считаются новыми. Бот постит весь каталог в каждый чат и звонит.
  - Строка `StarGift` появляется только после успешной отправки хотя бы в один чат. Если отправка падает во всех чатах, подарок остаётся «новым», и звонки повторяются на каждой итерации.
  - На каждой итерации выполняется N×M запросов `findUnique`, где N — подарки, M — чаты.

### Как определяют изменения (распродан, остаток)
- Снимок остатков в БД не хранится. Изменение определяется по тексту сообщения. `giftNotificationText(gift)` (gifts-radar.ts:174-207) заново строит текст из полей `limited`, `stars`, `availabilityRemains`, `availabilityTotal`. Этот текст сравнивается с сохранённым `infoMessageText` (:142-145). Если текст отличается, вызывается `client.editMessage(chatId, { message: infoMessageId, text, parseMode: 'html' })` (:146-150).
- Признак «распродан»: `availabilityRemains === 0` → хэштег `#soldout`, иначе `#instock`. Для `limited` добавляется ещё `#limited` (:200-205). Строка остатка: `📊 Stock: <remains> of <total> (<pct>%)`. При 0 % процент не выводится, потому что `if (percent)` ложно (:192-197). Заголовок «New (Limited) Telegram Gift!» при распродаже не меняется.
- Отдельного события «распродан» (звонка или нового сообщения) нет. Распродажа видна только через редактирование текста.
- Ошибка `MESSAGE_NOT_MODIFIED` проглатывается молча, остальные ошибки логируются (:113-128).

### Редактирование уведомлений и миграция `notification_editing`
- Миграция `20250127054334_notification_editing` добавляет `ALTER TABLE "StarGiftNotification" ADD COLUMN "editing" BOOLEAN NOT NULL DEFAULT true;`. В схеме это `editing Boolean @default(true)` (schema.prisma:23).
- Условие редактирования: `else if (editExisting && notification.editing)` (gifts-radar.ts:113). Флаг выключает редактирование для конкретного уведомления. В коде нигде не выставляется `editing = false`. Видимо, его меняют вручную в БД, например чтобы перестать трогать старые распроданные подарки и не тратить запросы. Коммит `b5e0bd3`: «feat: enable editing on specific notifications».
- Баг, выведенный из кода: после успешного `editMessage` поле `infoMessageText` в БД не обновляется (gifts-radar.ts:138-152, после edit записи в БД нет). Поэтому после первого изменения остатка сравнение «текст изменился» всегда истинно, и на каждой 5-й итерации уходит лишний `editMessage`. Если текст совпадает с тем, что уже стоит в сообщении, приходит `MESSAGE_NOT_MODIFIED`, и он подавляется.
- История подхода (коммит `3ce9391` «fix bug», 2025-01-26): раньше бот на каждой итерации пытался редактировать сообщение, а при любой ошибке, кроме `MESSAGE_NOT_MODIFIED`, удалял оба старых сообщения (`deleteMessages … revoke: true`) и отправлял новые. Эту схему убрали. Сейчас `deleteMessageNoThrow` (:132-136) нигде не вызывается.
- Сравнение с нашей идеей «ПРОДАНО»: механизм тот же. Храним `(chat_id, message_id, последний_текст)` на каждое уведомление, при изменении состояния перестраиваем текст и делаем `editMessageText`. Расхождения с тем, что нужно нам: у них `#soldout` вычисляется из данных, а не приходит отдельным событием; последний текст после правки не сохраняется (баг); правки троттлятся только счётчиком итераций; флаг `editing` позволяет перестать обновлять конкретное сообщение.

### Схема БД (Prisma, PostgreSQL)
Из schema.prisma:10-26:

| Модель | Поле | Тип | Примечание |
|---|---|---|---|
| `StarGift` | `giftId` | `BigInt @id` | id подарка магазина |
| | `notification` | `StarGiftNotification[]` | обратная связь |
| `StarGiftNotification` | `giftId` | `BigInt` | FK → `StarGift.giftId` |
| | `gift` | `StarGift @relation` | |
| | `chatId` | `String` | |
| | `giftMessageId` | `Int` | id сообщения со стикером |
| | `infoMessageId` | `Int` | id текстового сообщения, его и редактируют |
| | `infoMessageText` | `String` | текст при отправке |
| | `editing` | `Boolean @default(true)` | разрешено ли редактирование |
| | | `@@id([giftId, chatId])` | составной PK |

Три миграции:
1. `20250109015441_init`: создаёт таблицу `StarGiftNotification` (`giftId BIGINT`, `chatId TEXT`, `giftMessageId INTEGER`, `infoMessageId INTEGER`, `infoMessageText TEXT`, PK `(giftId, chatId)`).
2. `20250114184705_star_gift`: создаёт таблицу `StarGift(giftId BIGINT PK)`, заполняет её `SELECT DISTINCT "giftId"` из уведомлений и добавляет FK `StarGiftNotification.giftId → StarGift.giftId` (`ON DELETE RESTRICT ON UPDATE CASCADE`).
3. `20250127054334_notification_editing`: добавляет колонку `editing BOOLEAN NOT NULL DEFAULT true`.

Цены, остатки, история остатков и время появления подарка в БД не хранятся. Единственный «снимок» состояния — текст сообщения.

### Авторизация и сессия
- Пользовательская сессия GramJS. Конфиг: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_APP_VERSION`, `TELEGRAM_DEVICE_MODEL`, `TELEGRAM_SYSTEM_VERSION`; `langCode`/`systemLangCode` = `'en'` (main.ts:11-25, 50-68). Опционально SOCKS4/5-прокси из `PROXY` (main.ts:47, 60-66).
- Сессия: первым аргументом в `new TelegramClient(...)` передаётся строка-путь `path.join('sessions', env.TELEGRAM_SESSION_FILENAME)` (main.ts:48-51). Объект `StoreSession` или `StringSession` явно не создаётся. Папка `./sessions` монтируется в контейнер (docker-compose.yml:9) и лежит в `.gitignore`. Вход интерактивный: номер, пароль и код через `@inquirer/prompts` (utils.ts:8-22). README предлагает войти в интерактивном контейнере, затем запустить фоновый. Будет ли такая строка файловой сессией, зависит от поведения GramJS. В клоне нет `node_modules`, поэтому по коду не проверено (см. «Открытые вопросы»).
- Секретов в репозитории нет, в `.env.example` поля пустые.

### Уведомления / UI
- В чат идут два сообщения на подарок: стикер (`.tgs` через `downloadMedia` + `uploadFile` с именем `maxktz.tgs`, всегда беззвучно) и HTML-текст (gifts-radar.ts:154-172, 209-217).
- Баг: флаг `silent` для текста считается как `notification !== undefined`, но `findUnique` возвращает `null`, поэтому `silent` всегда `true` (gifts-radar.ts:77). Получается, что все сообщения в чат приходят беззвучно, а «громкий» канал — это звонки.
- Звонки (notifications-service.ts): `phone.requestCall` с протоколом layer 92. Через 30 с (`callDeclineDelay = 30_000`) вызывается `discardCall`. Если в ответе нет `phoneCall`, это считается «пользователь отклонил, т.е. заметил». Если не заметил, через 3 с звонок повторяется, потом идёт звонок через Twilio с TwiML «New Telegram Gifts Notification.». `CALL_RECIPIENTS` — это JSON вида `[{id, phone}]` (main.ts:38-45).
- Баги в звонках: в `getShagA` цикл `while (a <= 1 && a >= p)` не выполняется ни разу, поэтому `a = 0` и `g_a = 1` (notifications-service.ts:127-132). Звонку это не мешает, он нужен только чтобы зазвонил телефон. `sendCallNotifications` передаёт в `Promise.all` массив внутри массива, поэтому звонки фактически не дожидаются (:19-21).

### Остальные пункты шаблона
- Оценка/флор, комиссии, покупка/продажа: не применимо, проект ничего не покупает и не оценивает. В коде не найдено.
- Предохранители и лимиты: только фиксированная пауза 10 с и редактирование раз в 5 итераций. Обработки `FLOOD_WAIT`, backoff и throttle на `sendMessage`/`editMessage` в коде не найдено.
- Хранение состояния: PostgreSQL через Prisma (`DATABASE_URL`), миграции командой `bunx prisma migrate deploy` (package.json:10).

## Расхождения со старым отчётом (по зеркалам)
| Пункт | Старый отчёт | По исходникам |
|---|---|---|
| Частота опроса | 30 с (README) | 10 с (gifts-radar.ts:13). 30 с было только в первом коммите. Правки раз в 5 итераций |
| Метод | «вероятно `payments.getStarGifts`» | подтверждено, `hash: 0` всегда |
| Последняя активность | push 2025-01-25 (ecosyste.ms) | последний коммит 2025-01-27 07:53 +0200 (`1ec0fc7`) |
| Звёзды / форки / коммиты | 5 / 0 / не установлено | звёзды и форки не установлены (API закрыт), коммитов 25 |
| Хранение состояния | «снимок подарков в БД, сравнение» | в БД только id подарков и id/текст сообщений. Изменения находят сравнением сгенерированного текста |
| Публикация | в чаты `CHAT_IDS` и канал t.me/giftsradar | код постит только в `CHAT_IDS`. Канал упомянут лишь в README, вероятно он один из этих чатов (не установлено) |
| Апгрейды | не установлено | не отслеживаются, в коде нет |
| Звонки (Telegram + Twilio) | не упомянуты | есть, это основной канал «тревоги» о новом подарке |
| Лицензия | MIT (файл не открывался) | MIT подтверждена (LICENSE:1-3) |

## Что берём
| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Таблица уведомлений с ключом `(объект, chat_id)` и полями `message_id`, `last_text`, `editing` | `models/` (SQLAlchemy/Alembic), `bot/` | Идея. Переписываем и обязательно обновляем `last_text` после успешной правки |
| Правка пуша через `editMessageText` при смене состояния (у них остаток/`#soldout`, у нас «ПРОДАНО») + флаг, который отключает правку для старых сообщений | `bot/` | Идея. Игнорировать `MESSAGE_NOT_MODIFIED`, троттлить правки |
| Детект нового подарка магазина: `payments.getStarGifts` и сравнение множества `id` с сохранёнными | будущий воркер «новые подарки» (не MVP) | Идея. Лучше передавать `hash` из прошлого ответа, чтобы получать `StarGiftsNotModified` |
| Поля `limited`, `stars`, `availabilityRemains`, `availabilityTotal` у `StarGift` | там же | Формат API (из кода, не проверено на живом ответе) |
| Эскалация «тревоги»: Telegram-звонок → повтор → телефон | идея на потом | Только как идея. Для нас, скорее всего, лишнее |

## Что НЕ берём и почему
- Код: TypeScript/Bun/Prisma, а у нас Python. Код не копируем (AGENTS.md §4.3), хотя MIT это и разрешила бы.
- Опрос с `hash: 0` раз в 10 с без обработки FLOOD_WAIT: противоречит AGENTS.md §4.5.
- Схему «удалить и переотправить сообщение при ошибке правки» сам автор убрал в `3ce9391`.
- Звонки через `phone.requestCall` с поддельным `g_a`: хрупко, это злоупотребление API звонков, к флипу не относится.
- Юзербот, который постит в каналы с личной сессии: наш бот шлёт пуши только владельцу.

## Открытые вопросы
- Сессия: превращает ли GramJS `^2.26.x` строку-путь в первом аргументе `TelegramClient` в файловую сессию, или это сессия в памяти, и тогда после перезапуска контейнера нужен повторный вход? Без исходников библиотеки не проверено.
- Точная версия GramJS из `bun.lockb`: файл бинарный, не открывался.
- Звёзды и форки: не установлены.
- Откуда автор менял `editing = false` (вручную в БД?): в коде не найдено.
- Совпадают ли поля `StarGift` в текущем слое TL с использованными (`availabilityRemains`, `availabilityTotal`, `limited`, `stars`): сверять по core.telegram.org, когда понадобится.

## Для MARKETS.md
Маркетов в проекте нет. Факты про MTProto для будущего модуля «новые подарки магазина»:
- `payments.getStarGifts(hash: int)` → `payments.StarGifts{ gifts: StarGift[] }`. Вызывается с `hash: 0`, т.е. всегда полный список (из кода, src/gifts-radar.ts:22-24). `StarGiftsNotModified` не обрабатывается (из кода).
- Используемые поля `StarGift`: `id` (long), `stars`, `limited` (bool), `availabilityRemains`, `availabilityTotal`, `sticker` (документ .tgs) (из кода, gifts-radar.ts:177-211). «Распродан» = `availabilityRemains === 0` (из кода, :201).
- Частота опроса у автора: 10 с + время обработки, правки сообщений раз в 5 итераций (из кода, gifts-radar.ts:13, 41, 56). README заявляет 30 с, это устарело.
- Обработки FLOOD_WAIT и backoff нет (в коде не найдено).
- Правка уведомления: `messages.editMessage` (через GramJS `editMessage`, `parseMode: 'html'`), ошибка `MESSAGE_NOT_MODIFIED` игнорируется (из кода, gifts-radar.ts:118-120, 146-150).
- Сессия: пользовательская (GramJS), API ID/hash и параметры устройства из `.env`, вход интерактивный (из кода, main.ts:11-25, utils.ts:8-22).
