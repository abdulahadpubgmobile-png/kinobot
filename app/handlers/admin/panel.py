import asyncio
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.states import BroadcastFSM
from app.database.queries.users import count_users, get_all_users
from app.database.queries.movies import count_movies, total_views, get_all_movies, delete_movie, MOVIES_PER_PAGE
from app.keyboards.inline import broadcast_confirm_keyboard, movies_list_keyboard, admin_panel_keyboard
from app.keyboards.reply import main_keyboard, cancel_keyboard

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Xabar saqlash uchun temp storage
_broadcast_data: dict = {}


# ─── STATISTIKA ──────────────────────────────────────────

@router.callback_query(F.data == "admin_stats")
async def stats_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    users = await count_users(session)
    movies = await count_movies(session)
    views = await total_views(session)

    await callback.message.edit_text(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"🎬 Kinolar: <b>{movies}</b>\n"
        f"👁 Jami ko'rishlar: <b>{views}</b>",
        parse_mode="HTML",
        reply_markup=admin_panel_keyboard(),
    )
    await callback.answer()


# ─── KINOLAR RO'YXATI (ADMIN) ────────────────────────────

@router.callback_query(F.data.startswith("admin_movies_"))
async def admin_movies_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split("_")[2])
    movies, total = await get_all_movies(session, page=page)

    if not movies:
        await callback.answer("🎬 Hozircha kinolar yo'q.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    import math
    total_pages = math.ceil(total / MOVIES_PER_PAGE) if total else 1
    kb = InlineKeyboardBuilder()
    for movie in movies:
        kb.button(text=f"🎬 {movie.title} [{movie.code}]", callback_data=f"admin_movie_{movie.id}")
    kb.adjust(1)

    if page > 1:
        kb.button(text="⬅️ Oldingi", callback_data=f"admin_movies_{page - 1}")
    kb.button(text=f"📄 {page}/{total_pages}", callback_data="page_info")
    if page < total_pages:
        kb.button(text="➡️ Keyingi", callback_data=f"admin_movies_{page + 1}")
    kb.adjust(2 if page > 1 and page < total_pages else 1)
    kb.button(text="🔙 Orqaga", callback_data="back_admin")
    kb.adjust(1)

    await callback.message.edit_text(
        f"🎬 <b>Kinolar ro'yxati</b> ({total} ta):",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_movie_"))
async def admin_movie_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    movie_id = int(callback.data.split("_")[2])
    from app.database.queries.movies import get_movie_by_id
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Tahrirlash", callback_data=f"admin_edit_{movie.id}")
    kb.button(text="🗑 O'chirish", callback_data=f"admin_delete_{movie.id}")
    kb.button(text="🔙 Orqaga", callback_data="admin_movies_1")
    kb.adjust(2, 1)

    await callback.message.edit_text(
        f"🎬 <b>{movie.title}</b>\n"
        f"📌 Kod: <code>{movie.code}</code>\n"
        f"📅 {movie.year or '—'} | 🌍 {movie.country or '—'}\n"
        f"🎭 {movie.genre or '—'}\n"
        f"👁 {movie.views} ko'rishlar",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_"))
async def admin_delete_confirm(callback: CallbackQuery, session: AsyncSession) -> None:
    movie_id = int(callback.data.split("_")[2])
    from app.database.queries.movies import get_movie_by_id
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        await callback.answer("❌ Kino topilmadi!", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, o'chirish", callback_data=f"admin_do_delete_{movie_id}")
    kb.button(text="❌ Yo'q, bekor qilish", callback_data=f"admin_movie_{movie_id}")
    kb.adjust(2)

    await callback.message.edit_text(
        f"⚠️ <b>Siz rostdan ham bu kinoni o'chirmoqchimisiz?</b>\n\n"
        f"🎬 {movie.title}\n"
        f"📌 Kod: <code>{movie.code}</code>\n\n"
        f"❗ Bu amalni ortga qaytarib bo'lmaydi!",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_do_delete_"))
async def admin_do_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    movie_id = int(callback.data.split("_")[3])
    deleted = await delete_movie(session, movie_id)
    if deleted:
        await callback.message.edit_text("✅ <b>Kino o'chirildi!</b>", parse_mode="HTML")
    else:
        await callback.answer("❌ Xatolik!", show_alert=True)
    await callback.answer()


@router.callback_query(F.data == "back_admin")
async def back_to_admin(callback: CallbackQuery) -> None:
    await callback.message.edit_text("🛡 <b>Admin Panel</b>", reply_markup=admin_panel_keyboard(), parse_mode="HTML")
    await callback.answer()


# ─── BROADCAST ────────────────────────────────────────────

@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BroadcastFSM.waiting_for_message)
    await callback.message.answer(
        "📢 <b>Broadcast</b>\n\nReklama xabarini yuboring (matn, rasm yoki video):",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(BroadcastFSM.waiting_for_message, F.text == "❌ Bekor qilish")
async def broadcast_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(BroadcastFSM.waiting_for_message)
async def broadcast_get_message(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    _broadcast_data[user_id] = message.message_id
    await state.set_state(BroadcastFSM.waiting_for_confirm)

    await message.answer(
        "✅ <b>Xabar tayyor!</b>\n\nYuborilsinmi?",
        parse_mode="HTML",
        reply_markup=broadcast_confirm_keyboard(),
    )


@router.callback_query(BroadcastFSM.waiting_for_confirm, F.data == "broadcast_confirm")
async def broadcast_confirm_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot) -> None:
    await state.clear()
    user_id = callback.from_user.id
    msg_id = _broadcast_data.pop(user_id, None)

    if not msg_id:
        await callback.answer("❌ Xabar topilmadi!", show_alert=True)
        return

    users = await get_all_users(session)
    sent = 0
    failed = 0

    await callback.message.edit_text("📤 Yuborilmoqda...")

    for user in users:
        try:
            await bot.copy_message(
                chat_id=user.telegram_id,
                from_chat_id=callback.message.chat.id,
                message_id=msg_id,
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await callback.message.edit_text(
        f"✅ <b>Broadcast yakunlandi!</b>\n\n"
        f"✅ Yuborildi: {sent}\n"
        f"❌ Yuborilmadi: {failed}",
        parse_mode="HTML",
    )


@router.callback_query(BroadcastFSM.waiting_for_confirm, F.data == "broadcast_cancel")
async def broadcast_cancel_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user_id = callback.from_user.id
    _broadcast_data.pop(user_id, None)
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")
    await callback.answer()
