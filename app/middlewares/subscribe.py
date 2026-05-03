from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database.db import async_session_maker
from app.database.queries.channels import get_all_channels


class ForceSubscribeMiddleware(BaseMiddleware):
    """
    Har bir message/callback oldidan user obunasini tekshiradi.
    Agar obuna bo'lmasa, kanalga o'tish tugmasini ko'rsatadi.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot = data["bot"]

        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
            if user is None:
                return await handler(event, data)

            # Admin tekshiruvi o'tkazilmaydi
            from app.config import config
            if user.id in config.admins:
                return await handler(event, data)

            # Kanallarni DB dan olish
            async with async_session_maker() as session:
                channels = await get_all_channels(session)

            if not channels:
                return await handler(event, data)

            # Har bir kanalda obunani tekshir
            not_subscribed = []
            for channel in channels:
                try:
                    member = await bot.get_chat_member(channel.channel_id, user.id)
                    if member.status in ("left", "kicked", "banned"):
                        not_subscribed.append(channel)
                except Exception:
                    not_subscribed.append(channel)

            if not_subscribed:
                kb = InlineKeyboardBuilder()
                for ch in not_subscribed:
                    kb.button(text=f"📢 {ch.channel_name}", url=ch.channel_link)
                kb.button(text="✅ Tekshirish", callback_data="check_subscribe")
                kb.adjust(1)

                text = "❌ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:"

                if isinstance(event, Message):
                    await event.answer(text, reply_markup=kb.as_markup())
                elif isinstance(event, CallbackQuery):
                    await event.answer("Avval kanallarga obuna bo'ling!", show_alert=True)
                    await event.message.answer(text, reply_markup=kb.as_markup())
                return  # handleri chaqirmaymiz

        return await handler(event, data)
