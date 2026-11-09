"""Интерактивный вход в Telegram для Telethon-сессии владельца (на ПК владельца, D-016).

`python -m app.tools.login` — спросит телефон, код и пароль 2FA в терминале.
Сессия сохраняется в `data/<TG_SESSION_NAME>.session` с правами 600. Ничего не логирует.
"""

from __future__ import annotations

import asyncio

from app.security import ensure_private_dir
from app.settings import get_settings


async def main() -> None:
    from telethon import TelegramClient

    s = get_settings()
    if s.tg_api_id is None or s.tg_api_hash is None:
        raise SystemExit("нет TG_API_ID/TG_API_HASH в .env")
    ensure_private_dir(s.data_dir)
    client = TelegramClient(
        str(s.tg_session_path.with_suffix("")), s.tg_api_id, s.tg_api_hash.get_secret_value()
    )
    await client.start()
    me = await client.get_me()
    await client.disconnect()
    s.tg_session_path.chmod(0o600)
    print(f"Сессия сохранена: {s.tg_session_path} (600), аккаунт id={me.id}")


if __name__ == "__main__":
    asyncio.run(main())
