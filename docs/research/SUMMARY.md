# Сводка Этапа 0 (исследование)

Дата: 2026-11-09. Статус: **ЧАСТИЧНО** — часть источников прочитать не удалось (см. §1).

> Как читать статусы. «README» = прочитана главная страница репозитория или страница PyPI (через WebFetch, это пересказ мелкой моделью, а не дословный текст). «Код» = исходники. Ни один исходный файл на этом проходе не читался: `gh api` и `raw.githubusercontent.com` в сессии закрыты, клонировать правилами проекта нельзя. Ничего не запускалось, не клонировалось и не скачивалось. Ни одна цифра комиссии не проверена на практике.

## 1. Что реально прочитано

| Репо / источник | Задание | Что прочитано | Отчёт |
|---|---|---|---|
| topcvetok/telegram-gift-watch | A | **не прочитано** (доступ закрыт) | `topcvetok__telegram-gift-watch.md` |
| bleach-hub/portalsmp | B | README (PyPI + страница GitHub); код нет | `bleach-hub__portalsmp.md` |
| bleach-hub/aportalsmp | B.4 | страница GitHub и PyPI; документация (gitbook) нет | `bleach-hub__aportalsmp.md` |
| bleach-hub/tonnelmp | C | README (PyPI + страница GitHub); код нет | `bleach-hub__tonnelmp.md` |
| TheBrainAir/amrkt | D | README (страница GitHub); код нет | `thebrainair__amrkt.md` |
| boostNT/MRKT-API | D, E | README (страница GitHub) | `boostNT__MRKT-API.md` |
| tgmrkt-api (PyPI) | D | почти ничего: страница PyPI закрыта, источников нет | `pypi__tgmrkt-api.md` |
| boostNT/Portals-API | E | README (пересказ) | `boostNT__Portals-API.md` |
| boostNT/Tonnel-API | E | README (пересказ) | `boostNT__Tonnel-API.md` |
| kloveren/morgan-gift-plugins | F | только главная страница; плагины (алиасы, спред, giftstat) **не прочитаны** | `kloveren__morgan-gift-plugins.md` |
| bohd4nx/gifts-buyer | G | **не прочитано** (только стороннее зеркало старой версии) | `bohd4nx__gifts-buyer.md` |
| maxktz/telegram-gifts-radar | H | зеркала README и ecosyste.ms (не первоисточник) | `maxktz__telegram-gifts-radar.md` |
| bohd4nx/gifts-tracker | H | **не прочитано** | `bohd4nx__gifts-tracker.md` |
| 5 «снайперов» (раздел I) | I | **не прочитано** ни одного | `OnyxTarantulaLoop__…`, `smashguidetram__…`, `watchflowguide__…`, `SilentOverlordBrace__…`, `Townkibarrier__…` |
| icfpztaorrmf/portals-nft-sniper, Kirilka4345/ton-telegram-gifts-sniper-bot, DAAMCS/gift-parser | J | **не прочитано**; «вероятная малварь» остаётся гипотезой задания, не вывод | соответствующие `.md` |
| Закрытые сервисы | K | только публичные веб-сведения; экранов и Telegram нет | `ux/README.md` |
| MTProto `payments.getUniqueStarGiftValueInfo` | 0.4 | схема и описания полей с core.telegram.org (через результаты поиска) + зеркала | §3 ниже, `MARKETS.md` |

Пропуски, которые мешают больше всего: **код покупки/продажи/баланса у всех трёх маркетов, логика флора и фильтров topcvetok, WebSocket Tonnel, идеи предохранителей из «снайперов»**.

## 2. Матрица «функция → откуда берём → наш модуль»

| Функция | Источник идеи | Наш модуль | Что уже известно | Статус |
|---|---|---|---|---|
| Клиент Portals: поиск, коллекции | boostNT/Portals-API, portalsmp | `markets/portals.py` | `GET /api/nfts/search`, `GET /api/collections`; пагинация `offset/limit` (≤100); заголовок `Authorization: tma <initData>` | эндпоинты поиска есть (README); схема ответа неизвестна |
| Клиент Portals: флоры, активность, покупка, листинг, офферы, баланс, вывод | portalsmp (имена функций) | `markets/portals.py` | Есть только имена функций и сигнатуры; пути и тела неизвестны | **пробел** (нужен код) |
| Клиент MRKT: листинги | boostNT/MRKT-API, amrkt | `markets/mrkt.py` | `POST api.tgmrkt.io/api/v1/gifts/saling`, курсор, `count` ≤ 20; `POST /api/v1/auth {"data": initData}` → `token` | эндпоинты есть (README) |
| Клиент MRKT: покупка, листинг, инвентарь, возврат, баланс, история/feed | amrkt, пакет `mrkts` (имена методов) | `markets/mrkt.py` | Имена методов и nanoTON; пути и тела неизвестны | **пробел** (нужен код) |
| Клиент Tonnel: листинги | boostNT/Tonnel-API, tonnelmp | `markets/tonnel.py` | `POST gifts2.tonnel.network/api/pageGifts`; `limit` ≤ 30; фильтры строкой JSON; нужен `curl_cffi impersonate` | эндпоинт есть (README) |
| Клиент Tonnel: покупка, листинг, баланс, история | tonnelmp (имена и параметры) | `markets/tonnel.py` | Параметры `buyGift/listForSale`; пути неизвестны | **пробел** |
| Tonnel WebSocket событий | topcvetok | `markets/tonnel.py` | не подтверждён ни одним прочитанным источником | **пробел**, в Этапе 2 работать polling |
| Получение `initData` / токенов | portalsmp, amrkt, boostNT | `markets/auth.py` (новый), Telethon | Portals: бот `portals`, short_name `market`; MRKT: `/auth`; Tonnel: `web-initData` из localStorage | идея ясна, детали Telethon проверить |
| Флор по сопоставимым, кластерный флор | topcvetok, «снайперы» | `pricing/floor.py` | ничего не прочитано; определение есть в AGENTS.md §8 | **пробел** — проектируем сами |
| Проверка продажами 24ч | topcvetok | `pricing/sales.py` | Источники продаж: MRKT `history/feed` (имена), Tonnel `saleHistory` (требует auth/можно пусто), Portals `marketActivity` (имя) | частично |
| Оценка Telegram | MTProto | `pricing/tg_value.py` | Метод проверен по документации (§3) | подтверждено |
| Комиссии, all-in, net | README tonnelmp (+10% к покупке), статьи | `pricing/fees.py` | противоречивые данные, ничего не проверено (`MARKETS.md` §5) | **не проверено** |
| Алиасы коллекций, спред | morgan-gift-plugins | `pricing/aliases.py` | не прочитано; сопоставление названий можно строить из `collections` каждого маркета | **пробел** |
| Красивые номера, монохром | topcvetok | `rules/traits.py` | не прочитано | **пробел** — проектируем сами |
| Режимы, предохранители, `/doctor` | требования AGENTS.md, «снайперы» (не прочитаны) | `execution/` | берём из AGENTS.md и D-003 | проектируем сами |
| Пуши + SOLD-обновление | topcvetok | `bot/` | не прочитано; в Bot API есть `editMessageText` (общеизвестно) | проектируем сами |
| Резервный источник флоров | morgan (Giftstat), GiftAsset API | `pricing/` | GiftAsset: единый API с флорами и мульти-маркет данными (заявлено на их странице) — зацепка, не проверена | идея |
| Новые подарки магазина | gifts-buyer, radar | (позже) | radar: опрос 30 с, GramJS, Prisma (по зеркалам) | не MVP |

## 3. Проверка MTProto: `payments.getUniqueStarGiftValueInfo`

Основано на страницах core.telegram.org (метод и конструктор, схема слоя 212), прочитанных через результаты поиска; прямое открытие страницы заблокировано allowlist; поля сверены с зеркалами (MadelineProto, Pyrogram-forks, gotd).

- Сигнатура: `payments.getUniqueStarGiftValueInfo#4365af6b slug:string = payments.UniqueStarGiftValueInfo`. Параметр один — `slug` коллекционного подарка (из `starGiftUnique`, то есть из ссылки на подарок).
- Доступно **только пользователям**, боты не могут. Схема доступна с **слоя 212**. Ошибка: `400 STARGIFT_SLUG_INVALID`.
- Результат `payments.uniqueStarGiftValueInfo#512fe446`: `currency` (string, фиатная валюта по ISO 4217), `value` (long, оценочная стоимость), `initial_sale_date`, `initial_sale_stars`, `initial_sale_price`; необязательные: `last_sale_date`, `last_sale_price`, `floor_price`, `average_price`, `listed_count`, `fragment_listed_count`, `fragment_listed_url`; флаги `last_sale_on_fragment`, `value_is_average` (значение посчитано как среднее по проданным подаркам того же типа, иначе — по цене продажи этого подарка).
- Все суммы — «в наименьшей единице валюты `currency`», то есть **фиат (локализованная валюта аккаунта), а не TON и не Stars** (кроме `initial_sale_stars`). Для сопоставления с ценой в TON нужен курс, это добавляет погрешность.
- «Подарки того же типа» (`floor_price`, `average_price`, `listed_count`) — официальное описание не уточняет, коллекция это или модель/трейты. Нужна проверка на живых ответах.
- Практический вывод: годится как **вспомогательный независимый сигнал** (последняя/средняя цена продаж по данным Telegram и флор перепродаж в Telegram), но не как единственный флор. Нужны живая пользовательская сессия, слой Telethon ≥ 212 (проверка версии библиотеки не выполнялась) и slug каждого подарка.

## 4. Риски

1. **Неофициальные API.** Все эндпоинты — обратная разработка сайтов-Mini App; формат может меняться без предупреждения. Обёртки старые: portalsmp заархивирован 14.09.2025 (последний релиз 22.06.2025), tonnelmp — релиз 17.06.2025, aportalsmp — 24.11.2025. Им нельзя доверять как актуальной спецификации.
2. **Доступ и сроки токенов.** Срок жизни `initData`/токенов нигде не подтверждён (оценки: «более суток», 1–7 суток). Нужен перевыпуск по 401, а не расписание.
3. **ToS маркетов и Telegram.** Автоматизация клиентских сессий (Telethon, имитация браузера) может нарушать правила маркетов; возможна блокировка аккаунта или IP. Правила маркетов не читались.
4. **Защита от ботов.** Tonnel: обычные `requests/httpx` не работают, нужен `curl_cffi` с имитацией Chrome; сам механизм защиты не раскрыт. Может измениться.
5. **Комиссии не проверены и противоречивы** (`MARKETS.md` §5). Если расхождение «купить/продать» меньше суммарных комиссий, флип в минус. Пока нельзя считать честный net.
6. **Безопасность исполнителя.** Пользовательский `initData` и сессия Telethon дают доступ к аккаунту и кошельку; хранить только в секретах (AGENTS.md §4). «Снайперы» с .exe остаются непроверенной гипотезой задания, но правило «не запускать» в силе.
7. **Низкое качество публичных источников.** Статьи dev.to/ton-adoption — партнёрский контент, цифры противоречат друг другу; не использовать как источник комиссий.
8. **Гонки при покупке.** Листинг может исчезнуть/измениться между показом и покупкой; нужна запись «результат неизвестен» до запроса (требование плана Этапа 7).

## 5. Что нужно, чтобы закрыть Этап 0

Любое из двух (решение за владельцем проекта):

- (a) добавить `github.com`, `raw.githubusercontent.com`, `api.github.com` (и при желании `bleach-1.gitbook.io`, `core.telegram.org`) в allowlist сессии — тогда пройти исходники повторно по-прежнему только чтением;
- (b) явно разрешить `git clone --depth 1` в отдельные пустые каталоги **только для чтения как текст, без запуска и установки**, кроме репозиториев раздела I/J (их — только README).

Кроме того: UX-разбор закрытых сервисов (K) требует человека в Telegram — скриншоты и сценарии (см. `ux/README.md`).
