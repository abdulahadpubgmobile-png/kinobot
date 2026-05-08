from dataclasses import dataclass, field
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    admins: List[int]
    db_url: str
    channels: List[int]

    @classmethod
    def from_env(cls) -> "Config":
        bot_token = os.getenv("BOT_TOKEN", "")
        if not bot_token:
            raise ValueError("BOT_TOKEN muhit o'zgaruvchisi topilmadi!")

        admins_raw = os.getenv("ADMINS", "")
        admins = [int(a.strip()) for a in admins_raw.split(",") if a.strip()]

        # Render avtomatik DATABASE_URL beradi, agar bo'lmasa DB_URL yoki SQLite
        db_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL", "sqlite+aiosqlite:///./kinobot.db")
        # Render PostgreSQL URL ni asyncpg dialectiga o'tkazish
        if db_url:
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        channels_raw = os.getenv("CHANNELS", "")
        channels = [int(c.strip()) for c in channels_raw.split(",") if c.strip()]

        return cls(
            bot_token=bot_token,
            admins=admins,
            db_url=db_url,
            channels=channels,
        )


config = Config.from_env()
