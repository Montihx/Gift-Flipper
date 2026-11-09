# bohd4nx/gifts-tracker

> СТАТУС: РАЗБОР НЕ ВЫПОЛНЕН. Репозиторий прочитать не удалось (см. «Что не удалось»). Ниже нет ни одного факта о содержимом репо; все поля — «не установлено». Ничего не додумано.

- Ссылка: https://github.com/bohd4nx/gifts-tracker
- Язык / стек: не установлено
- Лицензия: не установлено
- Последний коммит / активность: не установлено
- Звёзды / форки / коммиты: не установлено
- Доверие: не оценено (данных нет)

## Что не удалось

Попытки чтения (все в режиме «только чтение»):
1. `gh api repos/bohd4nx/gifts-tracker` и `.../git/trees/HEAD`, `.../commits` — HTTP 403: «GitHub access to this repository is not enabled for this session».
2. WebFetch `https://github.com/bohd4nx/gifts-tracker` — URL_NOT_ON_ALLOWLIST.
3. WebFetch `https://raw.githubusercontent.com/bohd4nx/gifts-tracker/main/README.md` — URL_NOT_ON_ALLOWLIST.
4. WebSearch по «bohd4nx gifts-tracker» — страниц самого репозитория в выдаче нет (только соседний gifts-buyer, telegram-gifts-radar на ecosyste.ms и прочее).
5. WebFetch `awesome.ecosyste.ms/projects/github.com%2Fbohd4nx%2Fgifts-tracker` — URL_NOT_ON_ALLOWLIST.
6. Инструмент `add_repo` ответил, что публичные репо доступны через git-прокси только по `git clone`. Клонирование запрещено правилами задания, поэтому НЕ выполнялось.

## Как устроено

Не установлено (по заданию H нужны: частота опроса, определение новых подарков и улучшений, схема БД, формат уведомлений).

## Что берём
| Что | Куда у нас | Как |
|---|---|---|
| — | — | нет данных |

## Что НЕ берём и почему

Нечего оценивать. Приоритет задания 3, на MVP не влияет.

## Открытые вопросы

- Нужно разрешить чтение: добавить `github.com/bohd4nx/gifts-tracker` и `raw.githubusercontent.com` в allowlist WebFetch, либо разрешить `gh api` для этого репо (или явно разрешить shallow clone только для чтения, но без запуска кода).
- После этого повторить: README, структуру, схему БД, код опроса (интервал), логику «новый подарок / улучшение», шаблон уведомления, лицензию, дату последнего коммита, звёзды/форки/число коммитов.
- Второй репозиторий из задания H (maxktz/telegram-gifts-radar) разбирается отдельно. В поиске встретилась его страница на ecosyste.ms, но она не читалась.
