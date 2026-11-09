# Changelog

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/). Версии — после первого релиза.

## [Unreleased]

### Добавлено
- Этап 0: исследование API Portals, MRKT, Tonnel по исходникам открытых проектов (`docs/research/`, `docs/MARKETS.md`).
- Этап 1: каркас `backend/` (Python 3.12, настройки, nanoTON-деньги, UTC-время, маскирование секретов в логах, модели `listings`/`sales`, миграция Alembic `0001`) и `webapp/` (React + Vite). CI: ruff, pytest, проверка миграций на PostgreSQL, сборка Mini App.

### Безопасность
- `DRY_RUN=true` по умолчанию; `DRY_RUN=false` отклоняется при загрузке настроек до разрешения Этапа 7.
