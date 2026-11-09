# icfpztaorrmf/portals-nft-sniper

Источник: только README (raw-копия, скачана координатором 2026-11-09; refs: только `main`). Репозиторий не клонировался, ссылки не открывались. Остальные файлы репозитория (`assets/`, релизы, страница github.io) не читались по решению владельца проекта (задание J: только README).

Локальная копия README обрывается на ~14,5 КБ (строка 214, раздел «Fire Path Modules»). Разделы из оглавления «Usage guidelines», «LLM-Assisted Intent Engine», «Known Issues», «Roadmap», «FAQ» не прочитаны.

- Ссылка: https://github.com/icfpztaorrmf/portals-nft-sniper
- Язык / стек: по README «.NET 8 native build, single `.exe`», Windows 10/11 (README, стр. 47, 114)
- Лицензия: в README есть только бейдж `license-MIT` (стр. 28). Файл LICENSE не проверялся.
- Последний коммит / активность: не установлено. По README «Release 2026», «Updated for 2026».
- Звёзды / форки / коммиты: не установлено
- Доверие: **ПОДОЗРИТЕЛЬНО, вероятная малварь-приманка** (обоснование ниже)

## Что делает (по README)
README описывает Windows-`.exe` «mint sniper» для маркета Portals. Программа якобы следит за **mempool Ethereum mainnet**, заранее подписывает транзакции, симулирует их через `eth_call`, управляет газом и переключает RPC (Alchemy/Infura) (README, стр. 46, 77, 83, 108–114, 204–210).

## Как устроено (по README)
- Источник данных: «Any Ethereum mainnet RPC», WebSocket-подписка `newPendingTransactions` (модуль `mempool-ws`, стр. 207). К реальному Portals это отношения не имеет: Portals работает как Telegram Mini App на TON, у его листингов нет mempool, это off-chain API.
- Авторизация: при первом запуске мастер настройки просит «import wallet key path (or connect hardware)» (стр. 144). Ключ хранится в «Vault (encrypted keystore)» (стр. 170).
- Модель подарка, флор, комиссии, эндпоинты покупки: в README не описаны. Есть только общие слова про floor и bundle.
- Предохранители: горячие клавиши `F9` («panic stop»), Arm/disarm (стр. 185, 184). Они относятся к самому `.exe`, кода нет.

## Признаки малвари
| Признак | Что в README |
|---|---|
| `.exe` / архив / релиз | Да. «Standalone .exe Release», «Portable `.exe` via project page → download», «Extract the archive», «Launch the `.exe`» (стр. 9, 14, 75, 85, 142–144). |
| Внешние домены для скачивания | `icfpztaorrmf.github.io` (кнопка «GET Portals NFT Sniper 2026», стр. 151). Кроме того, «project page (linked in the release signature)» (стр. 142). Декоративные: `img.shields.io`, `readme-typing-svg.herokuapp.com`, `skillicons.dev`. Не открывались. |
| Обход защиты ОС | Инструкция «SmartScreen → More info → Run anyway». Сборки «не подписаны» (стр. 155). |
| Seed / приватный ключ / сессия / api_hash | Просит путь к ключу кошелька («import wallet key path», стр. 144) и предлагает «hot wallet pool» (стр. 108). Seed, Telegram-сессия и api_hash в прочитанной части не упоминаются. |
| «mempool» для off-chain маркета | Да: `mempool-ws`, «watches the mempool», газ, eth_call, Ethereum mainnet. Для Portals (TON, off-chain) это невозможно. Текст шаблонный и подходит к любому «NFT sniper». |
| Обфусцированные команды | В прочитанной части нет (ни PowerShell, ни base64). |
| Накрутка | По README не проверить. Есть признаки шаблона: маркетинговые бейджи «build passing», «status active», «39 modules», при этом исходников по README нет, только `.exe`. |

## Что берём
| Что | Куда у нас | Как |
|---|---|---|
| — | — | Ничего. Технического содержания про Portals нет. |

## Что НЕ берём и почему
Всё. README описывает Ethereum, а не Portals/TON. Распространяется неподписанный `.exe` через внешнюю страницу, а пользователя просят импортировать ключ кошелька. Это типичная схема дроппера или стилера. Ничего не скачивать и не запускать (AGENTS.md §4 п. 3).

## Открытые вопросы
Нет. Глубже не разбирать.

## Для MARKETS.md
- Фактов об API Portals нет (из README). Репо пометить в SUMMARY как «опасное, вероятная малварь».
