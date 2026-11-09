# boostNT/Tonnel-API

> Источник: клон от 2026-11-09, коммит `688d68f` (688d68f5e955f9a31a639d4e1db660a1f19e4fd2). В репозитории только `README.md` (144 строки), читался как текст. Живых запросов не было: всё ниже — «из README» (строки README.md), сверка — с кодом bleach-hub/tonnelmp `68064f7` (задание C).

- Ссылка: https://github.com/boostNT/Tonnel-API
- Язык / стек: только документация на русском + пример на Python (`curl_cffi`, `fake_useragent`).
- Лицензия: **нет** (файла LICENSE нет, в README не указана). Код не копируем.
- Последний коммит / активность: 2026-02-07 (`688d68f`) — удалены 3 строки (дисклеймер и контакт), содержание API не менялось. Последнее содержательное изменение — 2025-06-17. Первый коммит — 2025-05-15.
- Звёзды / форки / коммиты: звёзды/форки не установлено (в прошлой версии отчёта со слов страницы GitHub: 16 / 0, не перепроверено). Коммитов 15 (история полная, меньше лимита клона 50).
- Доверие: **среднее**. Только текст, бинарников и кода нет. Описан один эндпоинт; автор — тот же boostNT, которого tonnelmp благодарит за «403 fix» (tonnelmp README:109,119), и заголовки tonnelmp 1.2 совпадают с этим README один в один.

## Что делает (2–3 предложения)

Неофициальная документация к одному эндпоинту Tonnel — `POST https://gifts2.tonnel.network/api/pageGifts` (список листингов), с разбором полей `filter`/`sort`/`price_range`/`user_auth` и рабочим примером на `curl_cffi`. Покупка, продажа, баланс, авторизация не описаны; в конце ссылка на bleach-hub/tonnelmp как на «полноценную либку» (README:144).

## Как устроено
- Источник данных: только `POST https://gifts2.tonnel.network/api/pageGifts` (README:10, 135). Polling; WebSocket не упоминается. Частота опроса не указана.
- Тело (README:18-25, 124-131):

| Поле | Тип | Пример | Заметка |
|---|---|---|---|
| `page` | int | `1` | страница |
| `limit` | int | `5` | > 30 → `{'error': 'limit is too big'}` (README:31) |
| `sort` | **строка** JSON | `'{"message_post_time":-1,"gift_id":-1}'` | `json.dumps`, значения 1 / -1 |
| `filter` | **строка** JSON | см. ниже | `json.dumps` |
| `price_range` | список или `None` | `[1,1000]` | `None` = без фильтра (README:58) |
| `user_auth` | str | `''` | «обязательное поле», пустая строка = без входа (README:59) |

- Фильтр (README:45-56): фиксированная часть `price` exists, `refunded` ≠ true, `buyer` not exists, `export_at` exists; опционально `gift_name`, `model`, `backdrop`, `pattern`; значения — точная строка с редкостью (`"Albino (1.5%)"`), regex `{"$regex": "^Albino \\("}`, список `{"$in": [...]}` или regex-альтернатива `^(A|B)`; в конце `asset`: `TON`/`TONNEL`/`USDT`.
- Сортировки (README:36-42): `message_post_time`, `export_at`, `price`, `gift_num`, `modelRarity`/`backdropRarity`/`symbolRarity`, `rarity` и `gift_id` («неизвестно»).
- Защита (README:65, 81-97, 135): `requests`/`httpx` «не подойдут», нужен `curl_cffi` с `impersonate="chrome"` и случайный UA из `fake_useragent`. Заголовки: `authority: gifts2.tonnel.network`, `accept: */*`, `accept-encoding: gzip, deflate, br, zstd`, `accept-language: ru-RU,...`, `content-type: application/json`, `origin: https://market.tonnel.network`, `priority: u=1, i`, `referer: https://market.tonnel.network/`, `sec-ch-ua` (Chrome 137), `sec-ch-ua-mobile: ?0`, `sec-ch-ua-platform: "Windows"`, `sec-fetch-dest: empty`, `sec-fetch-mode: cors`, `sec-fetch-site: same-site`, `user-agent`. Cookies нет. В истории (2025-06-17) ранее был фиксированный UA Chrome 135 вместо случайного.
- Авторизация: только поле `user_auth`; что туда класть для залогиненного пользователя — не описано.
- Модель данных, оценка/флор, комиссии, покупка/продажа, предохранители, уведомления, хранение состояния: в README отсутствуют. Ответ не описан (пример просто печатает `response.json()`).

## Сверка с bleach-hub/tonnelmp (код `tonnelmp/marketapi.py`)

| Пункт | boostNT (README) | tonnelmp (код) | Вывод |
|---|---|---|---|
| URL поиска | `gifts2.tonnel.network/api/pageGifts` | тот же (`marketapi.py:76`) | совпадает |
| `filter`/`sort` как JSON-строки | да | да (`json.dumps`, `marketapi.py:161,164`) | совпадает |
| `price_range` «без фильтра» | `None` | `0` (`marketapi.py:172`) | **расхождение**; какое значение принимает сервер — проверить (оба, видимо, работали) |
| поле `ref` | нет | `ref: 0` (`marketapi.py:165`; `references.txt:11`) | **расхождение**; tonnelmp повторяет фронтенд |
| фильтр по узору | `pattern` | `symbol` (`marketapi.py:151-155`, `references.txt:35-37`, поле ответа `symbol`) | **расхождение, boostNT, вероятно, ошибается**: в БД поле `symbol` (и сорт `symbolRarity`) |
| смысл `export_at` | «время выставления» | «mint_time»; README tonnelmp:182 — «когда подарок можно минтить» | **расхождение**, верить tonnelmp |
| `rarity` в сорте | «неизвестно» | «rarity score» (`marketapi.py:89`) | уточнение |
| число сортировок | «их всего 10», перечислено 9 ключей | 10 пресетов на 8 ключах (`marketapi.py:84-95`) | по сути совпадает |
| `$in` и regex-альтернатива | описаны | в коде не используются | только из README boostNT, не проверено |
| `limit` > 30 | ошибка `limit is too big` | «максимум 30, as far as i know» | согласуется |
| `user_auth` | обязательное, `''` = гость | `""` по умолчанию; `initData` для `myGifts` | согласуется |
| impersonate | `"chrome"` (последний профиль curl_cffi) | `"chrome110"` | **расхождение**; профиль надо выбирать один и согласовывать с UA/`sec-ch-ua` |
| заголовки | набор выше | тот же набор (tonnelmp 1.2 взял отсюда) | совпадает |
| ссылка на сайт | `tonnel-gift.vercel.app` (README:3) | `market.tonnel.network` (Origin/Referer, README tonnelmp:48) | **расхождение**; рабочий фронтенд по обоим — `market.tonnel.network` (заголовки boostNT тоже его) |
| покупка/продажа/баланс/флоры/история | нет | есть (см. отчёт C) | boostNT покрывает только поиск |
| WebSocket | нет | нет | — |

## Что берём
| Что | Куда у нас | Как |
|---|---|---|
| Подтверждение формата `pageGifts` (`filter`/`sort` строками, `limit` ≤ 30, ответ-ошибка `limit is too big`) | `docs/MARKETS.md#tonnel`, `markets/tonnel.py` | формат API; основной источник — tonnelmp |
| Фильтр по нескольким значениям `{"$in": [...]}` | `markets/tonnel.py` | идея, проверить вживую (в tonnelmp нет) |

## Что НЕ берём и почему
- Пример кода: лицензии нет, и он тривиален.
- `pattern` как имя поля и трактовку `export_at` как «время выставления» — противоречат коду tonnelmp.
- `impersonate="chrome"` без фиксации версии — профиль меняется с версией curl_cffi; у нас версия профиля должна быть зафиксирована и согласована с заголовками.

## Открытые вопросы
- `price_range`: `None` или `0`; нужен ли `ref: 0`.
- Работает ли `$in`/regex-альтернатива в фильтре.
- Актуальность эндпоинта и заголовков на сегодня (содержание не менялось с 2025-06).

## Для MARKETS.md
- Подтверждает (из README, совпадает с кодом tonnelmp): `POST https://gifts2.tonnel.network/api/pageGifts`, `filter`/`sort` — JSON-строки, `limit` ≤ 30 (иначе `{'error': 'limit is too big'}`), `user_auth: ""` для гостя, curl_cffi + браузерные заголовки с `Origin/Referer: https://market.tonnel.network`.
- Расхождения с tonnelmp: `price_range` `None` (boostNT) vs `0` (tonnelmp); `ref: 0` есть только в tonnelmp; фильтр узора `pattern` (boostNT) vs `symbol` (tonnelmp — верно по коду и полям ответа); `export_at` = время минта (tonnelmp), а не листинга; impersonate `chrome` vs `chrome110`.
- Только у boostNT (не проверено): мультивыбор `{"$in": [...]}` и regex `^(A|B)` в фильтре.
- Лицензии нет; покупка/продажа/баланс/WS не описаны.
