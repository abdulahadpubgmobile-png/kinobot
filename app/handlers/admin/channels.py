from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.database.queries.channels import get_all_channels, add_channel, remove_channel
from app.keyboards.reply import cancel_keyboard, main_keyboard

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# FSM — handler tashqarisida e'lon qilinadi
class AddChannelFSM(StatesGroup):
    waiting_for_id = State()
    waiting_for_link = State()
    waiting_for_name = State()


async def _show_channels_list(callback: CallbackQuery, session: AsyncSession) -> None:
    channels = await get_all_channels(session)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()

    if channels:
        text = "📡 <b>Kanallar ro'yxati:</b>\n\n"
        for ch in channels:
            text += f"• {ch.channel_name} (<code>{ch.channel_id}</code>)\n"
            kb.button(text=f"🗑 {ch.channel_name}", callback_data=f"del_ch_{ch.id}")
        kb.adjust(1)
    else:
        text = "📡 Hozircha kanallar yo'q."

    kb.button(text="➕ Kanal qo'shish", callback_data="add_channel_start")
    kb.button(text="🔙 Orqaga", callback_data="back_admin")
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "admin_channels")
async def channels_list(callback: CallbackQuery, session: AsyncSession) -> None:
    await _show_channels_list(callback, session)
    await callback.answer()


@router.callback_query(F.data.startswith("del_ch_"))
async def remove_channel_callback(callback: CallbackQuery, session: AsyncSession) -> None:
    from app.database.models import Channel
    from sqlalchemy import select
    ch_id = int(callback.data.split("_")[2])
    result = await session.execute(select(Channel).where(Channel.id == ch_id))
    ch = result.scalar_one_or_none()
    if ch:
        await session.delete(ch)
        await session.commit()
    await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
    await _show_channels_list(callback, session)


@router.callback_query(F.data == "add_channel_start")
async def add_channel_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddChannelFSM.waiting_for_id)
    await callback.message.answer(
        "📡 <b>Kanal qo'shish — 1/3</b>\n\n"
        "Kanal ID sini yuboring:\n"
        "<i>Masalan: <code>-1001234567890</code></i>\n\n"
        "💡 ID ni bilish uchun kanalga @userinfobot ni qo'shing.",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(AddChannelFSM.waiting_for_id, F.text == "❌ Bekor qilish")
@router.message(AddChannelFSM.waiting_for_link, F.text == "❌ Bekor qilish")
@router.message(AddChannelFSM.waiting_for_name, F.text == "❌ Bekor qilish")
async def channel_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())


@router.message(AddChannelFSM.waiting_for_id)
async def channel_get_id(message: Message, state: FSMContext) -> None:
    try:
        channel_id = int(message.text.strip())
    except ValueError:
        await message.answer("⚠️ Noto'g'ri format! Raqam kiriting, masalan: <code>-1001234567890</code>", parse_mode="HTML")
        return
    await state.update_data(channel_id=channel_id)
    await state.set_state(AddChannelFSM.waiting_for_link)
    await message.answer(
        "📡 <b>Kanal qo'shish — 2/3</b>\n\nKanal havolasini yuboring:\n<i>Masalan: <code>https://t.me/kanalim</code></i>",
        parse_mode="HTML",
    )


@router.message(AddChannelFSM.waiting_for_link)
async def channel_get_link(message: Message, state: FSMContext) -> None:
    await state.update_data(channel_link=message.text.strip())
    await state.set_state(AddChannelFSM.waiting_for_name)
    await message.answer(
        "📡 <b>Kanal qo'shish — 3/3</b>\n\nKanal nomini yuboring:\n<i>Masalan: <code>KinoBot Kanali</code></i>",
        parse_mode="HTML",
    )


@router.message(AddChannelFSM.waiting_for_name)
async def channel_get_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    await state.clear()
    channel = await add_channel(
        session,
        channel_id=data["channel_id"],
        channel_link=data["channel_link"],
        channel_name=message.text.strip(),
    )
    await message.answer(
        f"✅ <b>{channel.channel_name}</b> kanali qo'shildi!\n🆔 ID: <code>{channel.channel_id}</code>",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )
