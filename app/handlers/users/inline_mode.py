from aiogram import Router, F
from aiogram.types import (
    InlineQuery, InlineQueryResultArticle,
    InputTextMessageContent,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.queries.movies import search_movies, get_movie_by_code

router = Router()


@router.inline_query()
async def inline_search(query: InlineQuery, session: AsyncSession) -> None:
    search_text = query.query.strip()
    bot_username = query.bot.username if query.bot else None

    if not search_text:
        await query.answer(
            results=[],
            switch_pm_text="Kino qidirish uchun bosing",
            switch_pm_parameter="start",
            cache_time=30,
        )
        return

    # Kod bo'yicha qidirish
    movie = await get_movie_by_code(session, search_text)
    if movie:
        results = [format_movie_article(movie, bot_username)]
        await query.answer(results, cache_time=30, is_personal=True)
        return

    # Nomi bo'yicha qidirish
    movies, total = await search_movies(session, search_text, page=1)

    if not movies:
        await query.answer(
            results=[],
            switch_pm_text="Hech narsa topilmadi. Bosh menyu",
            switch_pm_parameter="start",
            cache_time=30,
        )
        return

    results = []
    for movie in movies[:50]:  # Telegram max 50 results
        results.append(format_movie_article(movie, bot_username))

    await query.answer(results, cache_time=30, is_personal=True)


def format_movie_article(movie, bot_username: str = None) -> InlineQueryResultArticle:
    """Kino uchun inline natija (Article)."""
    kb = InlineKeyboardBuilder()
    if bot_username:
        kb.button(
            text="🎬 Kinoni olish",
            url=f"https://t.me/{bot_username}?start=movie_{movie.code}"
        )

    text = f"🎬 <b>{movie.title}</b>\n"
    if movie.year:
        text += f"📅 Yil: {movie.year}\n"
    if movie.genre:
        text += f"🎭 Janr: {movie.genre}\n"
    text += f"📌 Kod: <code>{movie.code}</code>"

    return InlineQueryResultArticle(
        id=str(movie.id),
        title=f"🎬 {movie.title} ({movie.year or '?'})",
        description=f"{movie.genre or ''} | Kod: {movie.code}",
        input_message_content=InputTextMessageContent(
            message_text=text,
            parse_mode="HTML",
        ),
        reply_markup=kb.as_markup() if bot_username else None,
    )
