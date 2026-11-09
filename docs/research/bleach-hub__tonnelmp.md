# bleach-hub/tonnelmp

> СТАТУС ОТЧЁТА: НЕПОЛНЫЙ. Исходники и README на GitHub прочитать не удалось (см. «Что не удалось прочитать»). Ниже только то, что подтверждено страницей PyPI. Эндпоинты, заголовки, поля и подпись НЕ описаны, чтобы ничего не додумывать.

- Ссылка: https://github.com/bleach-hub/tonnelmp (PyPI: https://pypi.org/project/tonnelmp/)
- Язык / стек: Python (на PyPI: Python 3.8+). Остальной стек (HTTP-клиент, curl_cffi и т.п.) — не удалось выяснить.
- Лицензия: MIT (заявлено на странице PyPI; файл LICENSE в репозитории не проверен)
- Последний коммит / активность: коммиты не проверены. Единственная проверенная дата — релиз tonnelmp 1.2 на PyPI от 17 июня 2025 г. (это дата релиза, не коммита).
- Звёзды / форки / коммиты: не удалось получить (нет доступа к GitHub API/веб-странице)
- Доверие: среднее (предварительно). Автор «bleach» тот же ник, что у portalsmp; лицензия MIT; у релиза на PyPI нет данных о происхождении (provenance). Исходники не просмотрены, поэтому оценка не окончательная.

## Что делает (2–3 предложения)
Python-модуль-обёртка над API маркетплейса Tonnel («A Python Module for interacting with Tonnel Marketplace API»). Для большинства функций нужен `authData`, который пользователь копирует из локального хранилища браузера (заявлено на PyPI).

## Как устроено
- Источник данных: эндпоинты — НЕ УДАЛОСЬ ВЫЯСНИТЬ (на PyPI перечислены только имена Python-функций, URL нет). Polling/WebSocket — неизвестно.
- Авторизация: по данным PyPI, нужен `authData`, копируется вручную из localStorage браузера. Формат, подпись/шифрование, срок жизни — не выяснено.
- Модель данных подарка: есть класс `Gift` (обёртка над данными подарка). Поля (`gift_num`, `gift_id`, `model`, `backdrop`, `symbol`, `price`) и вопрос «цена без 10% комиссии» — не проверено.
- Оценка/флор: в списке методов есть `filterStats`, `filterStatsPretty` (по названию — статистика по фильтрам, возможно флоры); логика не прочитана.
- Комиссии: не проверено, цифр нет. (Заявление из AGENTS/REPO_ANALYSIS «цена в API без 10% комиссии» — непроверенное, подтвердить по коду не удалось.)
- Покупка/продажа: на PyPI перечислены методы (имена только): 
  - Подарки: `getGifts`, `myGifts`, `listForSale`, `cancelSale`, `unlockListing`, `buyGift`, `returnGift`, `mintGift`, `giftData`, `saleHistory`, `switchTransfer`, `filterStats`, `filterStatsPretty`
  - Аукционы: `getAuctions`, `createAuction`, `cancelAuction`, `placeBid`
  - Розыгрыши: `giveawayInfo`, `joinGiveaway`
  - Аккаунт: `info` (вероятно баланс/профиль — не подтверждено), `withdraw`
  Эндпоинты, тела запросов, обработка ошибок — не выяснено. Метод `transferGift` из задания в списке PyPI отсутствует (возможно, внутренний или называется иначе — не проверено).
- Базовый URL: не выяснено.
- Обход защиты (заголовки, TLS-отпечаток): не выяснено.
- Предохранители и лимиты: не выяснено.
- Уведомления / UI: нет (библиотека).
- Хранение состояния: не выяснено.

## Что берём
| Что | Куда у нас | Как (идея / переписать / формат API) |
|---|---|---|
| Перечень операций Tonnel (поиск, покупка, продажа, отмена, возврат, история продаж, аукционы, вывод) | `docs/MARKETS.md#tonnel` — чек-лист «что должен уметь клиент» | Только как список функций; реализацию взять после чтения исходников |
| Всё остальное (схема API, заголовки) | — | После повторного прохода с доступом к исходникам |

## Что НЕ берём и почему
- Пока ничего не отвергнуто: исходники не просмотрены. Методы аукционов, розыгрышей, `mintGift` для флипа в MVP, вероятно, не нужны (предположение по названиям).

## Открытые вопросы
- Базовый URL, эндпоинты поиска/покупки/продажи/баланса и формат запросов.
- Что такое `authData` Tonnel: сырой initData, токен или что-то подписанное/зашифрованное; срок жизни.
- Поля подарка и является ли `price` ценой без 10% комиссии покупателя.
- Как обходится защита Tonnel (заголовки, TLS-отпечаток, curl_cffi?).
- Есть ли в коде WebSocket/события.
- Дата последнего коммита, звёзды/форки/число коммитов, наличие LICENSE в репо.
- Сверка с boostNT/Tonnel-API (делает другой агент).

## Что не удалось прочитать
- `gh api repos/bleach-hub/tonnelmp...` — HTTP 403 («GitHub access to this repository is not enabled for this session»).
- WebFetch для github.com и raw.githubusercontent.com — отклонён (URL not on allowlist).
- `add_repo` предложил только `git clone`, что запрещено правилами задания; клон не выполнялся.
- WebSearch ничего релевантного по репозиторию не вернул.
- Единственный прочитанный источник — страница PyPI tonnelmp 1.2 (через WebFetch); она содержит только список методов, лицензию, дату релиза и ссылку на репозиторий.

## Дополнение (второй проход, координатор): главная страница репозитория

Прочитана через WebFetch `www.github.com/bleach-hub/tonnelmp` (пересказ инструментом, не дословно). Исходники всё ещё НЕ читались.

- Лицензия: MIT. Звёзды / форки / коммиты: 29 / 3 / 44. Файлы: `tonnelmp/`, `LICENSE`, `README.md`, `pyproject.toml`, `references.txt`, `setup.py`.
- `authData`: на `market.tonnel.network` открыть Local Storage и скопировать значение ключа `web-initData` целиком, то есть это сырой `initData` Mini App. `getGifts` и `getAuctions` работают без него; `saleHistory` — можно пустую строку.
- Поля подарка (из примера ответа `getGifts`, пересказ): `gift_num`, `customEmojiId`, `gift_id`, `name`, `model`, `asset`, `symbol`, `backdrop`, `availabilityIssued`, `availabilityTotal`, `backdropData`, `message_in_channel`, `price`, `status`, `limited`, `auction`, `export_at`; также `bundleData` (бандлы), `premarket`.
- Комиссия: ЗАЯВЛЕНО в README (не проверено на практике): `getGifts` — «price in TON without 10% fee»; для `buyGift` итог равен `price * 1.1`. Для `listForSale` про комиссию ничего нет.
- `buyGift`: `gift_id`, `price`, `authData`, `receiver` (int, опционально, автор помечает как не протестированный), `anonymously` (bool, False), `showPrice` (bool, False). `listForSale`: `gift_id`, `price`, `authData`; `gift_id` — внутренний ID Tonnel, не `gift_num`.
- Защита: прямого описания нет; в changelog — исправления 403, поддержка прокси, зависимость `fake_useragent`, имитация chrome110 для `joinGiveaway`. Согласуется с boostNT/Tonnel-API (curl_cffi `impersonate="chrome"`).
- Base URL на странице нет. По boostNT/Tonnel-API: `https://gifts2.tonnel.network/api/pageGifts`.
- Итог: ключевое для нас — `authData` = `web-initData`, цена в `getGifts` без 10%, `gift_id` ≠ `gift_num`. Эндпоинты покупки и продажи по-прежнему не известны.
