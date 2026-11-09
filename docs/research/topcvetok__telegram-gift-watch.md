# topcvetok/telegram-gift-watch

СТАТУС ОТЧЁТА: НЕ РАЗОБРАН. Ни одного файла репозитория прочитать не удалось (доступ заблокирован окружением). Ниже только факты о попытках; все поля шаблона не заполнены, ничего не додумывалось.

- Ссылка: https://github.com/topcvetok/telegram-gift-watch
- Язык / стек: не удалось прочитать
- Лицензия: не удалось прочитать
- Последний коммит / активность: не удалось прочитать
- Звёзды / форки / коммиты: не удалось прочитать
- Доверие: не определено (код не видел)

## Что пробовали (2026-11-09)
| Способ | Результат |
|---|---|
| `gh api repos/topcvetok/telegram-gift-watch` (и commits, git/trees) | HTTP 403: "GitHub access to this repository is not enabled for this session" |
| WebFetch https://github.com/topcvetok/telegram-gift-watch | URL_NOT_ON_ALLOWLIST |
| WebFetch https://raw.githubusercontent.com/topcvetok/telegram-gift-watch/HEAD/README.md | URL_NOT_ON_ALLOWLIST |
| curl к raw.githubusercontent.com и api.github.com через прокси | CONNECT tunnel failed, 403 |
| WebSearch "topcvetok telegram-gift-watch github" | репозиторий в выдаче не найден |
| `add_repo` (read) | ответ: доступ read доступен только через `git clone --depth 1`; клон запрещён заданием, поэтому НЕ выполнялся |

## Задание A (9 пунктов)
Пункты 1-9 (флор, правило >=15%/>=5 соседей, медиана продаж 24ч, красивые номера/монохром, Tonnel WebSocket, Portals маршруты, MRKT feed/saling, антидубли и "ПРОДАНО", кэш флоров и SQLite) — не выполнены: исходников нет. Любые описания из задания (§2.A) являются заявлениями постановки, не проверенными фактами.

## Комиссии
Цифр комиссий не получено (проверено: нет, заявлено: нет).

## Как устроено / Что берём / Что НЕ берём
Не заполнено.

## Открытые вопросы
- Нужно либо разрешить доменам github.com / raw.githubusercontent.com / api.github.com в allowlist сессии (или включить `gh` для этого репо), либо явно разрешить `git clone --depth 1` в песочнице только для чтения (в обход правила "git clone запрещён" — решение за владельцем).
- После этого повторить разбор по пунктам 1-9.
