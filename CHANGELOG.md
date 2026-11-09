# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/). Версии — после первого релиза.

## [Unreleased]

### Добавлено
- Этап 0: исследование API Portals, MRKT, Tonnel по исходникам открытых проектов (`docs/research/`, `docs/MARKETS.md`).
- Этап 1: каркас `backend/` (Python 3.12, настройки, nanoTON-деньги, UTC-время, маскирование секретов в логах, модели `listings`/`sales`, миграция Alembic `0001`) и `webapp/` (React + Vite). CI: ruff, pytest, проверка миграций на PostgreSQL, сборка Mini App.
- Этап 2: клиенты Portals, MRKT, Tonnel только для чтения (поиск, флоры, продажи, события Tonnel), initData через Telethon, throttle/backoff/метрики, `MockClient`; `python -m app.engine --dry-run` печатает листинги (из фикстур; `--plan` — список живых запросов; `--live` — после разрешения владельца).

### Безопасность
- `DRY_RUN=true` по умолчанию; `DRY_RUN=false` отклоняется при загрузке настроек до разрешения Этапа 7.
- HTTP-слой маркетов пропускает только пути чтения из белого списка (D-017); живые запросы — только с `LIVE_READS_APPROVED=yes` (D-018).
