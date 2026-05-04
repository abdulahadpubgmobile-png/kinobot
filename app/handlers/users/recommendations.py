from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.queries.movies import get_recommendations
from app.keyboards.inline import movies_list_keyboard

router = Router()


@router.message(F.text == "🎬 Sizga tavsiya")
async def recommendations_handler(message: Message, session: AsyncSession) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not user_id:
        return

    movies = await get_recommendations(session, user_id, limit=10)

    if not movies:
        await message.answer(
            "🎬 <b>Hozircha tavsiyalar yo'q.</b>\n\n"
            "Kinolarni ko'ring va sevimlilarga qo'shing — shunda sizga mos kinolarni tavsiya qilamiz!",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer(
        f"🎬 <b>Sizga tavsiya etamiz</b> ({len(movies)} ta):",
        reply_markup=movies_list_keyboard(movies, len(movies), 1, prefix="rec_page"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("rec_page_"))
async def rec_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split("_")[2])
    user_id = callback.from_user.id if callback.from_user else 0
    movies = await get_recommendations(session, user_id, limit=50)

    if not movies:
        await callback.answer("🎬 Hozircha tavsiyalar yo'q.", show_alert=True)
        return

    import math
    per_page = 5
    total_pages = math.ceil(len(movies) / per_page) if movies else 1
    start = (page - 1) * per_page
    end = start + per_page
    page_movies = movies[start:end]

    from app.keyboards.inline import movies_list_keyboard
    await callback.message.edit_text(
        f"🎬 <b>Sizga tavsiya etamiz</b> ({len(movies)} ta):",
        reply_markup=movies_list_keyboard(page_movies, len(movies), page, prefix="rec_page"),
        parse_mode="HTML",
    )
    await callback.answer()


def main_keyboard():
    from app.keyboards.reply import main_keyboard as mk
    return mk()
