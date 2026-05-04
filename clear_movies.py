"""Barcha kinolarni va ularga bog'liq ma'lumotlarni o'chirish."""
import sys
import os

# Loyiha papkasini PATH ga qo'shamiz
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.db import async_session
from sqlalchemy import text


async def clear_all():
    async with async_session() as session:
        # Bog'liq jadvallarni tozalash
        await session.execute(text("DELETE FROM favorites"))
        await session.execute(text("DELETE FROM watch_history"))
        await session.execute(text("DELETE FROM ratings"))
        await session.execute(text("DELETE FROM movies"))
        await session.commit()
        print("✅ Barcha kinolar va bog'liq ma'lumotlar o'chirildi!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(clear_all())
