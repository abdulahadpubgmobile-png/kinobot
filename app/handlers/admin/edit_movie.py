from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.states import EditMovieFSM
from app.database.queries.movies import get_movie_by_id, update_movie
from app.keyboards.reply import cancel_keyboard, skip_keyboard
from app.keyboards.inline import back_keyboard

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

CANCEL_TEXT = "❌ Bekor qilish"


def edit_field_keyboard(movie_id: int) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎬 Nomi", callback_data=f"edit_field_title_{movie_id}")
    kb.button(text="📅 Yili", callback_data=f"edit_field_year_{movie_id}")
    kb.button(text="🌍 Davlat", callback_data=f"edit_field_country_{movie_id}")
    kb.button(text="🎭 Janri", callback_data=f"edit_field_genre_{movie_id}")
    kb.button(text="📝 Tavsif", callback_data=f"edit_field_description_{movie_id}")
    kb.button(text="🎥 Trailer", callback_data=f"edit_field_trailer_{movie_id}")
    kb.button(text="📹 Video", callback_data=f"edit_field_video_{movie_id}")
    kb.button(text="🖼 Poster", callback_data=f"edit_field_poster_{movie_id}")
    kb.button(text="✅ Tugatish", callback_data=f"admin_movie_{movie_id}")
    kb.adjust(2, 2, 2, 2, 1)
    return kb


@router.callback_query(F.data.startswith("admin_edit_"))
async def edit_movie_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    movie_id = int(callback.data.split("_")[2])
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    await callback.message.edit_text(
        f"✏️ <b>Kino tahrirlash</b>\n\n"
        f"🎬 {movie.title}\n"
        f"📌 Kod: <code>{movie.code}</code>\n\n"
        f"O'zgartirmoqchi bo'lgan maytni tanlang:",
        reply_markup=edit_field_keyboard(movie_id).as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── FIELD SELECTION ────────────────────────────────────────

@router.callback_query(F.data.startswith("edit_field_title_"))
async def edit_title(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split("_")[3])
    await state.update_data(movie_id=movie_id)
    await state.set_state(EditMovieFSM.waiting_for_title)
    await callback.message.edit_text(
        "🎬 <b>Yangi nomni yuboring:</b>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_year_"))
async def edit_year(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split("_")[3])
    await state.update_data(movie_id=movie_id)
    await state.set_state(EditMovieFSM.waiting_for_year)
    await callback.message.edit_text(
        "📅 <b>Yangi yilni yuboring:</b>",
        parse_mode="HTML",
        reply_markup=skip_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_country_"))
async def edit_country(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split("_")[3])
    await state.update_data(movie_id=movie_id)
    await state.set_state(EditMovieFSM.waiting_for_country)
    await callback.message.edit_text(
        "🌍 <b>Yangi davlatni yuboring:</b>",
        parse_mode="HTML",
        reply_markup=skip_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_genre_"))
async def edit_genre(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split("_")[3])
    await state.update_data(movie_id=movie_id)
    await state.set_state(EditMovieFSM.waiting_for_genre)
    await callback.message.edit_text(
        "🎭 <b>Yangi janrni yuboring:</b>",
        parse_mode="HTML",
        reply_markup=skip_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_description_"))
async def edit_description(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split("_")[3])
    await state.update_data(movie_id=movie_id)
    await state.set_state(EditMovieFSM.waiting_for_description)
    await callback.message.edit_text(
        "📝 <b>Yangi tavsifni yuboring:</b>",
        parse_mode="HTML",
        reply_markup=skip_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_trailer_"))
async def edit_trailer(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split("_")[3])
    await state.update_data(movie_id=movie_id)
    await state.set_state(EditMovieFSM.waiting_for_trailer)
    await callback.message.edit_text(
        "🎥 <b>Yangi trailer URL yuboring:</b>",
        parse_mode="HTML",
        reply_markup=skip_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_video_"))
async def edit_video(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split("_")[3])
    await state.update_data(movie_id=movie_id)
    await state.set_state(EditMovieFSM.waiting_for_video)
    await callback.message.answer(
        "📹 <b>Yangi video faylni yuboring:</b>",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field_poster_"))
async def edit_poster(callback: CallbackQuery, state: FSMContext) -> None:
    movie_id = int(callback.data.split("_")[3])
    await state.update_data(movie_id=movie_id)
    await state.set_state(EditMovieFSM.waiting_for_poster)
    await callback.message.answer(
        "🖼 <b>Yangi posterni yuboring:</b>",
        parse_mode="HTML",
        reply_markup=skip_keyboard(),
    )
    await callback.answer()


# ─── CANCEL ─────────────────────────────────────────────────

@router.message(EditMovieFSM.waiting_for_title, F.text == CANCEL_TEXT)
@router.message(EditMovieFSM.waiting_for_year, F.text == CANCEL_TEXT)
@router.message(EditMovieFSM.waiting_for_country, F.text == CANCEL_TEXT)
@router.message(EditMovieFSM.waiting_for_genre, F.text == CANCEL_TEXT)
@router.message(EditMovieFSM.waiting_for_description, F.text == CANCEL_TEXT)
@router.message(EditMovieFSM.waiting_for_trailer, F.text == CANCEL_TEXT)
@router.message(EditMovieFSM.waiting_for_video, F.text == CANCEL_TEXT)
async def cancel_edit(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    movie_id = data.get("movie_id")
    await state.clear()
    await message.answer(
        "❌ Tahrirlash bekor qilindi.",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


# ─── SAVE HANDLERS ─────────────────────────────────────────

@router.message(EditMovieFSM.waiting_for_title)
async def save_title(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    movie_id = data["movie_id"]
    await update_movie(session, movie_id, title=message.text.strip())
    await state.clear()
    await message.answer(
        "✅ Nomi yangilandi!",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_year)
async def save_year(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    movie_id = data["movie_id"]
    value = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await update_movie(session, movie_id, year=value)
    await state.clear()
    await message.answer(
        "✅ Yili yangilandi!",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_country)
async def save_country(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    movie_id = data["movie_id"]
    value = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await update_movie(session, movie_id, country=value)
    await state.clear()
    await message.answer(
        "✅ Davlat yangilandi!",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_genre)
async def save_genre(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    movie_id = data["movie_id"]
    value = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await update_movie(session, movie_id, genre=value)
    await state.clear()
    await message.answer(
        "✅ Janri yangilandi!",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_description)
async def save_description(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    movie_id = data["movie_id"]
    value = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await update_movie(session, movie_id, description=value)
    await state.clear()
    await message.answer(
        "✅ Tavsif yangilandi!",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_trailer)
async def save_trailer(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    movie_id = data["movie_id"]
    value = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await update_movie(session, movie_id, trailer_url=value)
    await state.clear()
    await message.answer(
        "✅ Trailer yangilandi!",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_video, F.video)
async def save_video(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    movie_id = data["movie_id"]
    await update_movie(session, movie_id, file_id=message.video.file_id)
    await state.clear()
    await message.answer(
        "✅ Video yangilandi!",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_video)
async def save_video_invalid(message: Message) -> None:
    await message.answer("⚠️ Iltimos, video fayl yuboring!")


@router.message(EditMovieFSM.waiting_for_poster, F.photo)
async def save_poster(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    movie_id = data["movie_id"]
    await update_movie(session, movie_id, poster_file_id=message.photo[-1].file_id)
    await state.clear()
    await message.answer(
        "✅ Poster yangilandi!",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_poster, F.text == "⏭ O'tkazib yuborish")
async def save_poster_skip(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    movie_id = data.get("movie_id")
    await state.clear()
    await message.answer(
        "❌ Bekor qilindi.",
        reply_markup=back_keyboard(f"admin_edit_{movie_id}").as_markup(),
    )


@router.message(EditMovieFSM.waiting_for_poster)
async def save_poster_invalid(message: Message) -> None:
    await message.answer("⚠️ Rasm yuboring yoki o'tkazib yuboring!")
