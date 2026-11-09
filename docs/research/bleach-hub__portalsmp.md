# bleach-hub/portalsmp

СТАТУС РАЗБОРА: НЕПОЛНЫЙ. Исходники и страница GitHub-репозитория прочитать не удалось (см. «Что не удалось прочитать»). Ниже только то, что реально видно на странице PyPI (README пакета) и в профиле автора на PyPI. Эндпоинты, тела запросов и формат цен из кода НЕ проверены и не выдуманы.

- Ссылка: https://github.com/bleach-hub/portalsmp (страница GitHub не прочитана); пакет: https://pypi.org/project/portalsmp/ (прочитано)
- Язык / стек: Python >=3.8 (PyPI). Для `update_auth()` — Pyrogram, начиная с 1.2 заменён на kurigram (PyPI, changelog).
- Лицензия: MIT (по метаданным PyPI; файл LICENSE в репозитории не проверен).
- Последний коммит / активность: НЕ УДАЛОСЬ ПРОЧИТАТЬ. Косвенно: последний релиз portalsmp 1.2 — 22 июня 2025 (PyPI). Что репозиторий архивирован — по заданию, на странице не подтверждено.
- Звёзды / форки / коммиты: НЕ УДАЛОСЬ ПРОЧИТАТЬ.
- Доверие: среднее (предварительно). Автор (PyPI `bleach`, регистрация 2 авг. 2024) выпускает три связанных пакета: portalsmp, aportalsmp, tonnelmp. Лицензия MIT, README без признаков малвари. Исходный код не смотрели, поэтому оценка по коду отсутствует.

## Что делает (2–3 предложения)

Python-модуль-обёртка над неофициальным API маркета Portals: поиск и флоры, активность, свои подарки и балансы, листинг, покупка, смена цены, офферы и коллекционные офферы, вывод. Все запросы требуют строку `authData`, начинающуюся с `tma`.

## Как устроено

(Всё ниже — из README на PyPI, файл исходников не читался.)

- Источник данных: базовый URL, пути и методы НЕ ПРОЧИТАНЫ. Известны только имена функций из README:
  - поиск и обзор: `search()`, `giftsFloors()`, `filterFloors()`, `collections()`, `marketActivity()`;
  - аккаунт: `myPortalsGifts()`, `myPoints()`, `myBalances()`, `myActivity()`;
  - листинг и торговля: `sale()`, `bulkList()` (в README помечена «Not tested yet»), `buy()`, `changePrice()`, `withdrawPortals()`;
  - офферы: `makeOffer()`, `cancelOffer()`, `editOffer()`, `topOffer()`, `myPlacedOffers()`, `myReceivedOffers()`;
  - коллекционные офферы: `collectionOffer()`, `cancelCollectionOffer()`, `allCollectionOffers()`, `myCollectionOffers()`.
- Параметры (README): `search()` и `marketActivity()` принимают сортировки `price_asc`, `latest`, `model_rarity_desc` и фильтры по имени подарка, модели, фону, символу и диапазону цены; имя и модель можно передавать списком. В `search()` `offset` — номер страницы, умноженный на `limit`. `makeOffer()`: `expiration_days` равен 0 (без срока) или 7. `withdrawPortals()`: README предупреждает, что адреса `UQ` могут работать только в виде `EQ`. Полный перечень фильтров и сортировок не получен.
- Авторизация (README, PyPI):
  - способ 1: скопировать заголовок `Authorization` из запроса к portals-market.com в сетевой вкладке браузера (Telegram Web); значение начинается с `tma`; README предупреждает, что токен может истечь примерно через 1–7 суток (заявлено автором, не проверено);
  - способ 2: `update_auth(api_id, api_hash)` — нужны `api_id` и `api_hash` с my.telegram.org и вход в Telegram; вызов `token = asyncio.run(update_auth(api_id, api_hash))`. Как именно код получает initData (какой бот и какой метод Pyrogram/kurigram) и как собирает строку `tma ...` — НЕ ПРОЧИТАНО.
- Модель данных подарка: есть класс `PortalsGift` (упомянут в changelog: в 1.0.1 из него убрали `owner_id`). Поля не прочитаны. В примере поиска из README цена приходит строкой: `"price": "44"`.
- Формат цен: README единицу и валюту не определяет; параметры функций типизированы `int|float`, в примере результата цена — строка `"44"`. Как цена передаётся в `buy()` и `sale()`, тело запроса `buy` — НЕ ПРОЧИТАНО. Из changelog: в 1.0.1 из `buy()` убран параметр `owner_id`.
- Оценка/флор: функции `giftsFloors()` и `filterFloors()` (добавлена в 1.2) существуют, формат ответа не прочитан.
- Комиссии: в README PyPI цифр комиссии нет. Заявленные в других источниках цифры (Portals 0% покупка / 5% продажа / 0.1 TON вывод) здесь не подтверждаются: «не проверено».
- Покупка/продажа: см. выше, тела запросов и обработка ошибок не прочитаны.
- Предохранители и лимиты: в README не обнаружены.
- Уведомления / UI: нет (библиотека).
- Хранение состояния: не прочитано (по README хранилища нет, токен возвращается вызывающему коду).

## Хронология версий (PyPI)

1.0 (14 июн 2025) — первая бета; 1.0.1 (17 июн) — убран `owner_id` из `buy()` и `PortalsGift`, починен `makeOffer()`; 1.1 (17 июн) — офферы; 1.1.1 — `topOffer()`; 1.1.2 (18 июн) — списки в `marketActivity()`; 1.1.3 (19 июн) — починен `cancelOffer()`; 1.1.4 (19 июн) — починен `marketActivity()`; 1.2 (22 июн) — `editOffer()`, `allCollectionOffers()`, `filterFloors()`, переход на kurigram.

## Ссылки на aportalsmp (пункт 4 — делает другой агент)

- На странице PyPI `portalsmp` упоминаний aportalsmp нет.
- В профиле автора на PyPI (https://pypi.org/user/bleach/) есть https://pypi.org/project/aportalsmp/ — «An Asynchronous Python Library for interacting with Portals Marketplace API», последний релиз 24 ноября 2025 (то есть свежее, чем portalsmp от 22 июня 2025). Тот же автор выпустил tonnelmp (последний релиз 17 июня 2025).
- Контакты автора из README: t.me/perfectlystill, чат разработчиков t.me/giftsdevschat.

## Что берём
| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Перечень операций Portals (имена функций, параметры search/marketActivity, сортировки) | `docs/MARKETS.md#portals` (как «заявлено, не проверено») | Использовать как чек-лист при реальном разборе исходников |
| Два способа получить `authData` (заголовок `Authorization: tma ...` из браузера; Telethon/Pyrogram-сессия) | `markets/portals.py`, `docs/MARKETS.md` | Наш вариант — Telethon-сессия владельца; сроки жизни токена 1–7 суток считать заявленными, проверить на практике |
| Фильтры `search()` принимают списки имён и моделей | `markets/portals.py` | Идея интерфейса, уточнить по коду |

## Что НЕ берём и почему
- Сам пакет не ставим и не запускаем (правила §4 AGENTS.md).
- Эндпоинты и тела запросов из этого отчёта брать нельзя: они не прочитаны.
- `bulkList()` — автор сам пишет «Not tested yet».

## Что не удалось прочитать
- Страница https://github.com/bleach-hub/portalsmp и raw.githubusercontent.com: WebFetch ответил `URL_NOT_ON_ALLOWLIST`, оба адреса недоступны в этой сессии.
- `gh api repos/bleach-hub/portalsmp...`: HTTP 403 «GitHub access to this repository is not enabled for this session»; повторный запрос по пути contents — HTTP 400. `add_repo` ответил, что доступны только анонимные git-чтения (clone), а клонировать запрещено заданием, поэтому не клонировал.
- Следовательно, не получены: лицензионный файл, дата последнего коммита, звёзды/форки/число коммитов, статус архива, исходники (`portalsmp/*.py`), любые эндпоинты, заголовки, тела `buy`/`sale`, формат цены в запросах, код `update_auth()`.
- WebSearch репозиторий не нашёл; прочитаны только PyPI-страницы (профиль автора и `portalsmp`).

## Открытые вопросы
- Нужен доступ к исходникам: добавить github.com / raw.githubusercontent.com `bleach-hub/portalsmp` в allowlist WebFetch или включить доступ `gh` к репозиторию, затем повторить пункты 1–3 задания B.
- Базовый URL API Portals, формат тела `buy` и единица цены (TON или nanoTON, строка или число) — не известны.
- Как `update_auth()` получает initData (запрос WebView к какому боту) и что хранится.
- Реальный срок жизни токена (заявлено 1–7 суток).
- Комиссии Portals — проверить на практике.

## Дополнение (второй проход, координатор): главная страница репозитория

Прочитана через WebFetch `www.github.com/bleach-hub/portalsmp` (пересказ инструментом, не дословно). Исходники всё ещё НЕ читались.

- Лицензия: MIT. Звёзды / форки / коммиты: 24 / 3 / 21. Репозиторий АРХИВИРОВАН владельцем 14 сентября 2025 (read-only).
- Корень репо: `portalsmp/`, `LICENSE`, `README.md`.
- Base URL API на странице нет (упомянут домен `portals-market.com` в инструкции для Telegram Web). По boostNT/Portals-API базовый URL — `https://portal-market.com/api`: домены различаются (`portals-market.com` в README portalsmp и `portal-market.com` в README boostNT) — проверить, какой верный.
- `authData`: заголовок `Authorization`, вида `tma <initData>`. `update_auth` — Pyrogram/kurigram, какой бот и метод — не указано (boostNT пишет: бот `portals`, short_name `market`).
- Цены: в примере строки (`"price": "44"`, `"floor_price": "31.43"`), единица не указана; параметры `price` в `sale/buy/changePrice` — `int|float`.
- Сигнатуры: `sale(nft_id, price, authData)`, `buy(nft_id, owner_id, price, authData)`; в changelog 1.0.1 `owner_id` из `buy()` удалён, но в документации он остаётся — расхождение.
- Срок токена: для Telegram Web «вероятно ограничен», оценка автора 1–7 суток; для `update_auth()` не указан.
- Итог: пункт 4 задания B закрыт частично (aportalsmp — отдельный отчёт). Архивирован → при расхождениях с живым API чинить придётся самим.
