from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.database.models import Movie, User, WatchHistory
from app.keyboards.inline import back_keyboard

router = Router()
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "admin_stats")
async def detailed_stats(callback: CallbackQuery, session: AsyncSession) -> None:
    """Batafsil statistika."""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())  # Hafta boshidan
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Asosiy statistikalar
    total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
    total_movies = (await session.execute(select(func.count(Movie.id)))).scalar_one()
    total_views = (await session.execute(select(func.sum(Movie.views)))).scalar_one() or 0

    # Bugungi statistikalar
    today_users = (
        await session.execute(
            select(func.count(User.id)).where(User.joined_at >= today_start)
        )
    ).scalar_one()
    today_movies = (
        await session.execute(
            select(func.count(Movie.id)).where(Movie.created_at >= today_start)
        )
    ).scalar_one()

    # Haftalik statistikalar
    week_users = (
        await session.execute(
            select(func.count(User.id)).where(User.joined_at >= week_start)
        )
    ).scalar_one()
    week_movies = (
        await session.execute(
            select(func.count(Movie.id)).where(Movie.created_at >= week_start)
        )
    ).scalar_one()

    # Oylik statistikalar
    month_users = (
        await session.execute(
            select(func.count(User.id)).where(User.joined_at >= month_start)
        )
    ).scalar_one()
    month_movies = (
        await session.execute(
            select(func.count(Movie.id)).where(Movie.created_at >= month_start)
        )
    ).scalar_one()

    # Eng ko'p ko'rilgan kinolar (Top 5)
    top_movies_result = await session.execute(
        select(Movie).order_by(desc(Movie.views)).limit(5)
    )
    top_movies = top_movies_result.scalars().all()

    # Eng faol foydalanuvchilar (Top 5)
    top_users_result = await session.execute(
        select(User, func.count(WatchHistory.id).label("watch_count"))
        .join(WatchHistory, WatchHistory.user_id == User.telegram_id)
        .group_by(User.id)
        .order_by(desc("watch_count"))
        .limit(5)
    )
    top_users = top_users_result.all()

    # Xabar matni
    text = f"📊 <b>Batafsil statistika</b>\n\n"
    text += f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
    text += f"🎬 Jami kinolar: <b>{total_movies}</b>\n"
    text += f"👁 Jami ko'rishlar: <b>{total_views}</b>\n\n"

    text += f"📅 <b>Bugun:</b>\n"
    text += f"  👥 Yangi foydalanuvchilar: {today_users}\n"
    text += f"  🎬 Yangi kinolar: {today_movies}\n\n"

    text += f"📅 <b>Shu hafta:</b>\n"
    text += f"  👥 Yangi foydalanuvchilar: {week_users}\n"
    text += f"  🎬 Yangi kinolar: {week_movies}\n\n"

    text += f"📅 <b>Shu oy:</b>\n"
    text += f"  👥 Yangi foydalanuvchilar: {month_users}\n"
    text += f"  🎬 Yangi kinolar: {month_movies}\n\n"

    if top_movies:
        text += f"🎬 <b>Eng ko'p ko'rilgan kinolar (Top 5):</b>\n"
        for i, movie in enumerate(top_movies, 1):
            text += f"  {i}. {movie.title} — {movie.views} ko'rish\n"
        text += "\n"

    if top_users:
        text += f"👥 <b>Eng faol foydalanuvchilar (Top 5):</b>\n"
        for i, (user, watch_count) in enumerate(top_users, 1):
            name = user.fullname or user.username or f"User {user.telegram_id}"
            text += f"  {i}. {name} — {watch_count} ko'rish\n"

    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Yangilash", callback_data="admin_stats")
    kb.button(text="🔙 Orqaga", callback_data="back_admin")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()
