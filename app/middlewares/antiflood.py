import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

# Foydalanuvchi so'nggi xabar vaqtini saqlash
_user_timestamps: Dict[int, float] = {}
RATE_LIMIT = 0.5  # sekundlarda


class AntiFloodMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            user_id = event.from_user.id
            now = time.monotonic()
            last = _user_timestamps.get(user_id, 0)

            if now - last < RATE_LIMIT:
                await event.answer("⏳ Iltimos, biroz kuting...")
                return

            _user_timestamps[user_id] = now

        return await handler(event, data)
