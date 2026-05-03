import math
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.queries.movies import (
    get_movie_by_code, get_movie_by_id, increment_views,
    search_movies, get_movies_by_genre, get_all_movies,
    get_all_genres, MOVIES_PER_PAGE,
)
from app.database.queries.favorites import (
    is_favorite, add_favorite, remove_favorite, get_user_favorites,
)
from app.keyboards.inline import movies_list_keyboard, genres_keyboard, movie_keyboard
from app.keyboards.reply import main_keyboard, cancel_keyboard
from app.states import SearchFSM

router = Router()

SKIP = ("🎬 Kinolar", "🔍 Qidirish", "🎭 Janrlar", "ℹ️ Yordam", "❌ Bekor qilish")


async def send_movie(message_or_callback, movie, session: AsyncSession, bot: Bot) -> None:
    await increment_views(session, movie.id)

    if isinstance(message_or_callback, Message):
        send = message_or_callback
    else:
        send = message_or_callback.message

    user_id = send.from_user.id if send.from_user else 0
    is_fav = await is_favorite(session, user_id, movie.id) if user_id else False

    if user_id:
        from app.database.queries.watch_history import add_watch_history
        await add_watch_history(session, user_id, movie.id)

    me = await bot.get_me()
    bot_link = f"https://t.me/{me.username}"
    bot_username = f"@{me.username}"

    genre_tags = ""
    if movie.genre:
        genre_tags = " ".join([f"#{g.strip().replace(' ', '_')}" for g in movie.genre.split(",")])

    caption = f"🎬 <b>{movie.title}</b>\n"
    caption += "━━━━━━━━━━━━━━━━━━\n"
    if movie.year:
        caption += f"📅 Yil: <b>{movie.year}</b>\n"
    if movie.country:
        caption += f"🌍 Davlat: <b>{movie.country}</b>\n"
    if movie.genre:
        caption += f"🎭 Janr: {genre_tags}\n"
    if movie.description:
        caption += f"\n📝 {movie.description}\n"
    caption += "━━━━━━━━━━━━━━━━━━\n"
    caption += f"🤖 Bizning bot: <a href=\"{bot_link}\">{bot_username}</a>"

    await send.answer_video(
        video=movie.file_id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=movie_keyboard(movie, is_fav),
        supports_streaming=True,
    )


@router.message(F.text & ~F.text.in_(SKIP), StateFilter(None))
async def get_movie_by_code_handler(message: Message, session: AsyncSession, state: FSMContext, bot: Bot) -> None:
    code = message.text.strip()
    movie = await get_movie_by_code(session, code)
    if movie:
        await send_movie(message, movie, session, bot)
    else:
        await message.answer(
            f"🔍 <b>{code}</b> kodli kino topilmadi.\n"
            "Qidiruv uchun 🔍 Qidirish tugmasini bosing.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )


@router.message(F.text == "🎬 Kinolar")
async def all_movies_handler(message: Message, session: AsyncSession) -> None:
    movies, total = await get_all_movies(session, page=1)
    if not movies:
        await message.answer("🎬 Hozircha kinolar mavjud emas.")
        return
    await message.answer(
        f"🎬 <b>Barcha kinolar</b> ({total} ta)\n\nKinoni tanlang:",
        reply_markup=movies_list_keyboard(movies, total, 1, prefix="all_page"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("all_page_"))
async def all_movies_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split("_")[2])
    movies, total = await get_all_movies(session, page=page)
    await callback.message.edit_text(
        f"🎬 <b>Barcha kinolar</b> ({total} ta)\n\nKinoni tanlang:",
        reply_markup=movies_list_keyboard(movies, total, page, prefix="all_page"),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("movie_"))
async def movie_detail_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    movie_id = int(callback.data.split("_")[1])
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        await callback.answer("❌ Kino topilmadi!", show_alert=True)
        return
    await send_movie(callback, movie, session, bot)
    await callback.answer()


@router.message(F.text == "🔍 Qidirish")
async def search_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchFSM.waiting_for_query)
    await message.answer(
        "🔍 <b>Qidiruv</b>\n\nKino nomi yoki kodini yozing:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )


@router.message(SearchFSM.waiting_for_query, F.text == "❌ Bekor qilish")
async def search_cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Qidiruv bekor qilindi.", reply_markup=main_keyboard())


@router.message(SearchFSM.waiting_for_query)
async def search_query_handler(message: Message, session: AsyncSession, state: FSMContext) -> None:
    query = message.text.strip()
    await state.clear()
    movies, total = await search_movies(session, query, page=1)
    if not movies:
        await message.answer(
            f"😔 <b>{query}</b> bo'yicha hech narsa topilmadi.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return
    await message.answer(
        f"🔍 <b>{query}</b> bo'yicha natijalar ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, 1, prefix="search_page", extra=query),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("search_page_"))
async def search_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split("_", 3)
    page = int(parts[2])
    query = parts[3] if len(parts) > 3 else ""
    movies, total = await search_movies(session, query, page=page)
    await callback.message.edit_text(
        f"🔍 <b>{query}</b> bo'yicha natijalar ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, page, prefix="search_page", extra=query),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.text == "🎭 Janrlar")
async def genres_handler(message: Message, session: AsyncSession) -> None:
    genres = await get_all_genres(session)
    if not genres:
        await message.answer("🎭 Hozircha janrlar mavjud emas.")
        return
    await message.answer(
        "🎭 <b>Janrlar</b>\n\nQaysi janrni ko'rmoqchisiz?",
        reply_markup=genres_keyboard(genres),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("genre_"))
async def genre_movies_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    genre = callback.data[6:]
    movies, total = await get_movies_by_genre(session, genre, page=1)
    if not movies:
        await callback.answer(f"😔 {genre} janrida kinolar topilmadi.", show_alert=True)
        return
    await callback.message.edit_text(
        f"🎭 <b>{genre}</b> janridagi kinolar ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, 1, prefix="genre_page", extra=genre),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("genre_page_"))
async def genre_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split("_", 3)
    page = int(parts[2])
    genre = parts[3] if len(parts) > 3 else ""
    movies, total = await get_movies_by_genre(session, genre, page=page)
    await callback.message.edit_text(
        f"🎭 <b>{genre}</b> janridagi kinolar ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, page, prefix="genre_page", extra=genre),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── FAVORITES ───────────────────────────────────────

@router.callback_query(F.data.startswith("fav_"))
async def toggle_favorite(callback: CallbackQuery, session: AsyncSession) -> None:
    movie_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    is_fav = await is_favorite(session, user_id, movie_id)

    if is_fav:
        await remove_favorite(session, user_id, movie_id)
        await callback.answer("🤍 Sevimlidan o'chirildi")
    else:
        await add_favorite(session, user_id, movie_id)
        await callback.answer("❤️ Sevimlilarga qo'shildi!")

    movie = await get_movie_by_id(session, movie_id)
    if movie:
        await callback.message.edit_reply_markup(reply_markup=movie_keyboard(movie, not is_fav))


@router.message(F.text == "❤️ Sevimlilar")
async def show_favorites(message: Message, session: AsyncSession) -> None:
    user_id = message.from_user.id
    movies = await get_user_favorites(session, user_id)
    if not movies:
        await message.answer(
            "🤍 Hozircha sevimli kinolaringiz yo'q.\nKino sahifasida ❤️ belgisini bosing.",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer(
        f"❤️ <b>Sevimli kinolaringiz</b> ({len(movies)} ta):",
        reply_markup=movies_list_keyboard(movies, len(movies), 1, prefix="fav_page"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("fav_page_"))
async def fav_page_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    movies = await get_user_favorites(session, user_id)
    total = len(movies)
    await callback.message.edit_text(
        f"❤️ <b>Sevimli kinolaringiz</b> ({total} ta):",
        reply_markup=movies_list_keyboard(movies, total, page, prefix="fav_page"),
        parse_mode="HTML",
    )
    await callback.answer()
