import asyncio
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.database.queries.series import (
    add_series, get_all_series, get_series_by_id,
    update_series, delete_series, get_series_with_parts,
)
from app.database.queries.movies import get_movie_by_id, add_movie, update_movie
from app.keyboards.reply import cancel_keyboard, skip_keyboard, main_keyboard
from app.keyboards.inline import admin_panel_keyboard

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddSeriesFSM(StatesGroup):
    waiting_for_title = State()
    waiting_for_total_parts = State()
    waiting_for_year = State()
    waiting_for_genre = State()
    waiting_for_description = State()
    waiting_for_poster = State()


class AddEpisodeFSM(StatesGroup):
    waiting_for_series = State()
    waiting_for_part_number = State()
    waiting_for_title = State()
    waiting_for_code = State()
    waiting_for_file = State()
    waiting_for_poster = State()
    waiting_for_year = State()
    waiting_for_genre = State()
    waiting_for_description = State()


CANCEL_TEXT = "❌ Bekor qilish"


# ─── SERIES MENU ─────────────────────────────────────

@router.callback_query(F.data == "admin_series")
async def series_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    series_list = await get_all_series(session)

    text = f"🎬 <b>Serialar boshqaruvi</b>\n\n"
    text += f"📦 Jami serialar: {len(series_list)}\n"

    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Yangi serial", callback_data="series_add_start")
    if series_list:
        kb.button(text="📋 Barcha serialar", callback_data="series_list_1")
    kb.button(text="🔙 Orqaga", callback_data="back_admin")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


# ─── SERIES LIST ─────────────────────────────────────

@router.callback_query(F.data.startswith("series_list_"))
async def series_list(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split("_")[2])
    series_list = await get_all_series(session)

    if not series_list:
        await callback.answer("🎬 Hozircha serialar yo'q.", show_alert=True)
        return

    import math
    per_page = 5
    total_pages = math.ceil(len(series_list) / per_page) if series_list else 1
    start = (page - 1) * per_page
    end = start + per_page
    page_series = series_list[start:end]

    kb = InlineKeyboardBuilder()
    for series in page_series:
        kb.button(text=f"🎬 {series.title} ({series.total_parts} qism)", callback_data=f"series_detail_{series.id}")
    kb.adjust(1)

    if page > 1:
        kb.button(text="⬅️ Oldingi", callback_data=f"series_list_{page - 1}")
    kb.button(text=f"📄 {page}/{total_pages}", callback_data="page_info")
    if page < total_pages:
        kb.button(text="➡️ Keyingi", callback_data=f"series_list_{page + 1}")
    kb.adjust(1)
    kb.button(text="🔙 Orqaga", callback_data="admin_series")
    kb.adjust(1)

    await callback.message.edit_text(
        f"🎬 <b>Serialar ro'yxati</b> ({len(series_list)} ta):",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("series_detail_"))
async def series_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    series_id = int(callback.data.split("_")[2])
    series, parts = await get_series_with_parts(session, series_id)

    if not series:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    text = f"🎬 <b>{series.title}</b>\n\n"
    text += f"📦 Qismlar soni: {series.total_parts}\n"
    if series.year:
        text += f"📅 Yil: {series.year}\n"
    if series.genre:
        text += f"🎭 Janr: {series.genre}\n"
    text += f"📝 Mavjud qismlar: {len(parts)}\n"

    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Tahrirlash", callback_data=f"series_edit_{series.id}")
    kb.button(text="🗑 O'chirish", callback_data=f"series_delete_{series.id}")
    kb.button(text="📋 Qismlar", callback_data=f"series_parts_{series.id}")
    kb.button(text="🔙 Orqaga", callback_data="series_list_1")
    kb.adjust(2, 1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("series_parts_"))
async def series_parts(callback: CallbackQuery, session: AsyncSession) -> None:
    series_id = int(callback.data.split("_")[2])
    series, parts = await get_series_with_parts(session, series_id)

    if not series:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    text = f"🎬 <b>{series.title}</b> - Qismlar:\n\n"

    kb = InlineKeyboardBuilder()
    for part in parts:
        text += f"{part.part_number}-qism: {part.title} [{part.code}]\n"
        kb.button(text=f"🎬 {part.part_number}-qism", callback_data=f"admin_movie_{part.id}")

    kb.adjust(1)
    kb.button(text="➕ Qism qo'shish", callback_data=f"episode_add_start_{series_id}")
    kb.button(text="🔙 Orqaga", callback_data=f"series_detail_{series_id}")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


# ─── ADD SERIES FSM ──────────────────────────────────

@router.callback_query(F.data == "series_add_start")
async def series_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddSeriesFSM.waiting_for_title)
    await callback.message.delete()
    await callback.message.answer(
        "🎬 <b>Yangi serial</b>\n\n"
        "1-qadam: Serial nomini yuboring:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(AddSeriesFSM.waiting_for_title)
async def series_get_title(message: Message, state: FSMContext) -> None:
    if message.text == CANCEL_TEXT:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddSeriesFSM.waiting_for_total_parts)
    await message.answer(
        "📦 2-qadam: Qismlar sonini yuboring (masalan: 10):",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddSeriesFSM.waiting_for_total_parts, F.text != CANCEL_TEXT)
async def series_get_total_parts(message: Message, state: FSMContext) -> None:
    try:
        total = int(message.text.strip())
        if total < 1:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Iltimos, musbat son yuboring!")
        return

    await state.update_data(total_parts=total)
    await state.set_state(AddSeriesFSM.waiting_for_year)
    await message.answer(
        "📅 3-qadam: Yilni yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddSeriesFSM.waiting_for_year, F.text != CANCEL_TEXT, F.text != "⏭ O'tkazib yuborish")
async def series_get_year(message: Message, state: FSMContext) -> None:
    year = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(year=year)
    await state.set_state(AddSeriesFSM.waiting_for_genre)
    await message.answer(
        "🎭 4-qadam: Janrni yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddSeriesFSM.waiting_for_genre, F.text != CANCEL_TEXT, F.text != "⏭ O'tkazib yuborish")
async def series_get_genre(message: Message, state: FSMContext) -> None:
    genre = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(genre=genre)
    await state.set_state(AddSeriesFSM.waiting_for_description)
    await message.answer(
        "📝 5-qadam: Tavsif yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddSeriesFSM.waiting_for_description, F.text != CANCEL_TEXT, F.text != "⏭ O'tkazib yuborish")
async def series_get_description(message: Message, state: FSMContext) -> None:
    desc = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddSeriesFSM.waiting_for_poster)
    await message.answer(
        "🖼 6-qadam: Poster yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddSeriesFSM.waiting_for_poster, F.photo)
async def series_get_poster(message: Message, state: FSMContext, session: AsyncSession) -> None:
    poster = message.photo[-1].file_id
    data = await state.get_data()

    series = await add_series(
        session,
        title=data["title"],
        total_parts=data["total_parts"],
        year=data.get("year"),
        genre=data.get("genre"),
        description=data.get("description"),
        poster_file_id=poster,
    )

    await state.clear()
    await message.answer(
        f"✅ <b>Serial qo'shildi!</b>\n\n"
        f"🎬 {series.title}\n"
        f"📦 Qismlar: {series.total_parts}",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


@router.message(AddSeriesFSM.waiting_for_poster, F.text == "⏭ O'tkazib yuborish")
async def series_skip_poster(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()

    series = await add_series(
        session,
        title=data["title"],
        total_parts=data["total_parts"],
        year=data.get("year"),
        genre=data.get("genre"),
        description=data.get("description"),
    )

    await state.clear()
    await message.answer(
        f"✅ <b>Serial qo'shildi!</b>\n\n"
        f"🎬 {series.title}\n"
        f"📦 Qismlar: {series.total_parts}",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


@router.message(AddSeriesFSM.waiting_for_poster)
async def series_invalid_poster(message: Message) -> None:
    if message.text == CANCEL_TEXT:
        await series_cancel(message, await FSMContext())
        return
    await message.answer("⚠️ Rasm yuboring yoki ⏭ bosing!")


# ─── ADD EPISODE FSM ───────────────────────────────

@router.callback_query(F.data.startswith("episode_add_start_"))
async def episode_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    series_id = int(callback.data.split("_")[3])
    await state.update_data(series_id=series_id)
    await state.set_state(AddEpisodeFSM.waiting_for_part_number)

    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Orqaga", callback_data=f"series_parts_{series_id}")
    kb.adjust(1)

    await callback.message.edit_text(
        "🎬 <b>Yangi qism</b>\n\n"
        "1-qadam: Qism raqamini yuboring (masalan: 1, 2, 3...):",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AddEpisodeFSM.waiting_for_part_number, F.text == CANCEL_TEXT)
async def episode_cancel_1(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddEpisodeFSM.waiting_for_part_number, F.text != CANCEL_TEXT)
async def episode_get_part_number(message: Message, state: FSMContext) -> None:
    try:
        part_number = int(message.text.strip())
        if part_number < 1:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Iltimos, musbat son yuboring!")
        return

    await state.update_data(part_number=part_number)
    await state.set_state(AddEpisodeFSM.waiting_for_title)
    await message.answer(
        "🎬 2-qadam: Qism nomini yuboring:",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddEpisodeFSM.waiting_for_title, F.text == CANCEL_TEXT)
async def episode_cancel_2(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddEpisodeFSM.waiting_for_title, F.text != CANCEL_TEXT)
async def episode_get_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AddEpisodeFSM.waiting_for_code)
    await message.answer(
        "🔤 3-qadam: Kino kodini yuboring (masalan: s1e1):",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddEpisodeFSM.waiting_for_code, F.text == CANCEL_TEXT)
async def episode_cancel_3(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddEpisodeFSM.waiting_for_code, F.text != CANCEL_TEXT)
async def episode_get_code(message: Message, state: FSMContext) -> None:
    await state.update_data(code=message.text.strip())
    await state.set_state(AddEpisodeFSM.waiting_for_file)
    await message.answer(
        "🎥 4-qadam: Kino faylini (video) yuboring:",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddEpisodeFSM.waiting_for_file, F.text == CANCEL_TEXT)
async def episode_cancel_4(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddEpisodeFSM.waiting_for_file, F.video)
async def episode_get_file(message: Message, state: FSMContext) -> None:
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddEpisodeFSM.waiting_for_poster)
    await message.answer(
        "🖼 5-qadam: Poster yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddEpisodeFSM.waiting_for_file)
async def episode_invalid_file(message: Message) -> None:
    if message.text == CANCEL_TEXT:
        await episode_cancel_4(message, await FSMContext())
        return
    await message.answer("⚠️ Video fayl yuboring!")


@router.message(AddEpisodeFSM.waiting_for_poster, F.text == CANCEL_TEXT)
async def episode_cancel_5(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddEpisodeFSM.waiting_for_poster, F.photo)
async def episode_get_poster(message: Message, state: FSMContext) -> None:
    await state.update_data(poster_file_id=message.photo[-1].file_id)
    await state.set_state(AddEpisodeFSM.waiting_for_year)
    await message.answer(
        "📅 6-qadam: Yilni yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddEpisodeFSM.waiting_for_poster, F.text == "⏭ O'tkazib yuborish")
async def episode_skip_poster(message: Message, state: FSMContext) -> None:
    await state.update_data(poster_file_id=None)
    await state.set_state(AddEpisodeFSM.waiting_for_year)
    await message.answer(
        "📅 6-qadam: Yilni yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddEpisodeFSM.waiting_for_poster)
async def episode_invalid_poster(message: Message) -> None:
    if message.text == CANCEL_TEXT:
        await episode_cancel_5(message, await FSMContext())
        return
    await message.answer("⚠️ Rasm yuboring yoki ⏭ bosing!")


@router.message(AddEpisodeFSM.waiting_for_year, F.text == CANCEL_TEXT)
async def episode_cancel_6(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddEpisodeFSM.waiting_for_year)
async def episode_get_year(message: Message, state: FSMContext) -> None:
    year = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(year=year)
    await state.set_state(AddEpisodeFSM.waiting_for_genre)
    await message.answer(
        "🎭 7-qadam: Janrni yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddEpisodeFSM.waiting_for_genre, F.text == CANCEL_TEXT)
async def episode_cancel_7(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddEpisodeFSM.waiting_for_genre)
async def episode_get_genre(message: Message, state: FSMContext) -> None:
    genre = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(genre=genre)
    await state.set_state(AddEpisodeFSM.waiting_for_description)
    await message.answer(
        "📝 8-qadam: Tavsif yuboring:",
        reply_markup=skip_keyboard(),
    )


@router.message(AddEpisodeFSM.waiting_for_description, F.text == CANCEL_TEXT)
async def episode_cancel_8(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddEpisodeFSM.waiting_for_description)
async def episode_get_description(message: Message, state: FSMContext, session: AsyncSession) -> None:
    desc = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    data = await state.get_data()

    movie = await add_movie(
        session,
        code=data["code"],
        title=data["title"],
        year=data.get("year"),
        genre=data.get("genre"),
        description=desc,
        file_id=data["file_id"],
        poster_file_id=data.get("poster_file_id"),
        series_id=data["series_id"],
        part_number=data["part_number"],
    )

    await state.clear()
    await message.answer(
        f"✅ <b>Qism qo'shildi!</b>\n\n"
        f"🎬 {movie.title}\n"
        f"📼 Kodi: {movie.code}\n"
        f"📦 Qism: {movie.part_number}",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


# ─── DELETE SERIES ────────────────────────────────────

@router.callback_query(F.data.startswith("series_delete_"))
async def series_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    series_id = int(callback.data.split("_")[2])

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, o'chirish", callback_data=f"series_do_delete_{series_id}")
    kb.button(text="❌ Yo'q", callback_data=f"series_detail_{series_id}")
    kb.adjust(2)

    await callback.message.edit_text(
        "⚠️ <b>Siz rostdan ham bu serialni o'chirmoqchimisiz?</b>\n"
        "Barcha qismlar bog'liqligi o'chadi.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("series_do_delete_"))
async def series_do_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    series_id = int(callback.data.split("_")[3])
    deleted = await delete_series(session, series_id)
    if deleted:
        await callback.message.edit_text("✅ Serial o'chirildi!")
    else:
        await callback.answer("❌ Xatolik!", show_alert=True)
    await series_menu(callback, session)


# ─── CANCEL (series) ─────────────────────────────────

@router.message(AddSeriesFSM.waiting_for_title, F.text == CANCEL_TEXT)
@router.message(AddSeriesFSM.waiting_for_total_parts, F.text == CANCEL_TEXT)
@router.message(AddSeriesFSM.waiting_for_year, F.text == CANCEL_TEXT)
@router.message(AddSeriesFSM.waiting_for_genre, F.text == CANCEL_TEXT)
@router.message(AddSeriesFSM.waiting_for_description, F.text == CANCEL_TEXT)
@router.message(AddSeriesFSM.waiting_for_poster, F.text == CANCEL_TEXT)
async def series_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())
