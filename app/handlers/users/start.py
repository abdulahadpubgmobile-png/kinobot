from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.queries.users import get_or_create_user
from app.keyboards.reply import main_keyboard
from app.keyboards.inline import admin_panel_keyboard
from app.filters import IsAdmin

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession, bot: Bot) -> None:
    user = message.from_user
    await get_or_create_user(
        session,
        telegram_id=user.id,
        fullname=user.full_name,
        username=user.username,
    )

    # Deep linking: /start movie_001
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        if param.startswith("movie_"):
            code = param[6:]  # "movie_001" -> "001"
            movie = await get_movie_by_code(session, code)
            if movie:
                from app.handlers.users.movies import send_movie
                await send_movie(message, movie, session, bot)
                return

    await message.answer(
        f"🎬 <b>Kino Botga xush kelibsiz!</b>\n\n"
        f"👤 Salom, <b>{user.first_name}</b>!\n\n"
        f"Kino kodini yuboring yoki qidiruv tugmasidan foydalaning.",
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message) -> None:
    await message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "🔹 Kino kodini yozing → Kino olasiz\n"
        "🔹 <b>🔍 Qidirish</b> → Kino nomi bo'yicha qidirish\n"
        "🔹 <b>🎭 Janrlar</b> → Janr bo'yicha ko'rish\n"
        "🔹 <b>🎬 Kinolar</b> → Barcha kinolar ro'yxati\n\n"
        "📌 Kino kodini to'g'ridan-to'g'ri yuboring!",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


@router.message(Command("admin"), IsAdmin())
async def admin_handler(message: Message) -> None:
    await message.answer(
        "🛡 <b>Admin Panel</b>",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "check_subscribe")
async def check_subscribe_callback(callback: CallbackQuery) -> None:
    await callback.answer("✅ Obuna tekshirildi! Endi botdan foydalanishingiz mumkin.", show_alert=True)
    await callback.message.delete()


@router.callback_query(F.data == "views_info")
async def views_info_callback(callback: CallbackQuery) -> None:
    await callback.answer("👁 Ko'rishlar soni", show_alert=False)


@router.callback_query(F.data == "page_info")
async def page_info_callback(callback: CallbackQuery) -> None:
    await callback.answer()
