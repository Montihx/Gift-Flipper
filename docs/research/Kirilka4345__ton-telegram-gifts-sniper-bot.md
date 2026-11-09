# Kirilka4345/ton-telegram-gifts-sniper-bot

- Ссылка: https://github.com/Kirilka4345/ton-telegram-gifts-sniper-bot
- Язык / стек: НЕ ПРОВЕРЕНО (исходники не прочитаны)
- Лицензия: НЕ ПРОВЕРЕНО
- Последний коммит / активность: НЕ ПРОВЕРЕНО
- Звёзды / форки / коммиты: НЕ ПРОВЕРЕНО (в AGENTS/REPO_ANALYSIS §2 J указано: 1 коммит, один файл `ton_gifts_sniper.py` — это данные из задания, не мои наблюдения)
- Доверие: НЕ ОЦЕНЕНО. По умолчанию считать ПОДОЗРИТЕЛЬНЫМ (шаблонный «снайпер», см. §2 I/J), но это не вывод из кода.

## Статус проверки

Прочитать репозиторий не удалось, отчёт по шаблону §1 не заполнен:

- `gh api repos/Kirilka4345/ton-telegram-gifts-sniper-bot/...` (repo, tree, commits, releases) -> HTTP 403: «GitHub access to this repository is not enabled for this session».
- WebFetch `github.com/Kirilka4345/...` и `raw.githubusercontent.com/.../ton_gifts_sniper.py` -> URL_NOT_ON_ALLOWLIST.
- `add_repo` ответил, что доступен только анонимный `git clone`. Клонирование запрещено правилами задания (§0 REPO_ANALYSIS: только чтение, без клонов), поэтому не выполнялось.

Не выяснено: источники данных (URL/API), куда уходят сессии/токены/сообщения, признаки малвари (base64/exec/eval, сторонние webhook/боты, отправка session-файлов), наличие README/релизов/.exe.

## Что нужно, чтобы закончить
Любое из: добавить `raw.githubusercontent.com` и `github.com` (или `api.github.com` для этого репо) в allowlist; либо явно разрешить shallow-клон в отдельный пустой каталог только для чтения файла как текста (без запуска).
