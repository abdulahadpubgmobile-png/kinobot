import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.database.queries.ads import (
    add_ad, get_all_ads, get_active_ads,
    delete_ad, deactivate_expired_ads, get_ad_by_id, update_ad,
)
from app.keyboards.reply import cancel_keyboard, skip_keyboard, main_keyboard
from app.keyboards.inline import admin_panel_keyboard

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class AddAdFSM(StatesGroup):
    waiting_for_text = State()
    waiting_for_media = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()
    waiting_for_duration = State()


# ─── ADS MENU ─────────────────────────────────────────

@router.callback_query(F.data == "admin_ads")
async def ads_menu(callback: CallbackQuery, session: AsyncSession) -> None:
    expired = await deactivate_expired_ads(session)
    ads = await get_all_ads(session)
    active_ads = await get_active_ads(session)

    text = f"📢 <b>Reklamalar boshqaruvi</b>\n\n"
    text += f"✅ Faol: {len(active_ads)}\n"
    text += f"📦 Jami: {len(ads)}\n"

    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Yangi reklama", callback_data="ad_add_start")
    kb.button(text="📋 Barcha reklamalar", callback_data="ad_list_1")
    kb.button(text="🔙 Orqaga", callback_data="back_admin")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


# ─── AD LIST ──────────────────────────────────────────

@router.callback_query(F.data.startswith("ad_list_"))
async def ad_list(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split("_")[2])
    ads = await get_all_ads(session)

    if not ads:
        await callback.answer("📢 Hozircha reklama yo'q.", show_alert=True)
        return

    import math
    per_page = 5
    total_pages = math.ceil(len(ads) / per_page) if ads else 1
    start = (page - 1) * per_page
    end = start + per_page
    page_ads = ads[start:end]

    kb = InlineKeyboardBuilder()
    for ad in page_ads:
        status = "✅" if ad.is_active else "⛔️"
        preview = ad.text[:30] + "..." if ad.text and len(ad.text) > 30 else (ad.text or "(rasm/video)")
        kb.button(text=f"{status} {preview}", callback_data=f"ad_detail_{ad.id}")
    kb.adjust(1)

    if page > 1:
        kb.button(text="⬅️ Oldingi", callback_data=f"ad_list_{page - 1}")
    kb.button(text=f"📄 {page}/{total_pages}", callback_data="page_info")
    if page < total_pages:
        kb.button(text="➡️ Keyingi", callback_data=f"ad_list_{page + 1}")
    kb.adjust(1)
    kb.button(text="🔙 Orqaga", callback_data="admin_ads")
    kb.adjust(1)

    await callback.message.edit_text(
        f"📢 <b>Reklamalar ro'yxati</b> ({len(ads)} ta):",
        reply_markup=kb.as_markup(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ad_detail_"))
async def ad_detail(callback: CallbackQuery, session: AsyncSession) -> None:
    ad_id = int(callback.data.split("_")[2])
    ad = await get_ad_by_id(session, ad_id)
    if not ad:
        await callback.answer("❌ Topilmadi!", show_alert=True)
        return

    now = datetime.now()
    if ad.is_active and ad.start_date <= now <= ad.end_date:
        status = "✅ Faol"
    elif not ad.is_active:
        status = "⛔️ O'chirilgan"
    else:
        status = "⛔️ Muddati o'tgan"

    start_str = ad.start_date.strftime("%Y-%m-%d %H:%M")
    end_str = ad.end_date.strftime("%Y-%m-%d %H:%M")

    text = f"📢 <b>Reklama</b>\n\n"
    text += f"📌 Holati: {status}\n"
    if ad.text:
        text += f"📝 Matn: {ad.text}\n"
    if ad.media_type:
        text += f"🎬 Turi: {ad.media_type}\n"
    if ad.button_text:
        text += f"🔗 Tugma: {ad.button_text}\n"
    text += f"📅 Boshlanishi: {start_str}\n"
    text += f"📅 Tugashi: {end_str}\n"

    kb = InlineKeyboardBuilder()
    if ad.is_active:
        kb.button(text="⛔️ O'chirish", callback_data=f"ad_deactivate_{ad.id}")
    else:
        kb.button(text="✅ Faollashtirish", callback_data=f"ad_activate_{ad.id}")
    kb.button(text="🗑 O'chirish", callback_data=f"ad_delete_{ad.id}")
    kb.button(text="🔙 Orqaga", callback_data="ad_list_1")
    kb.adjust(2, 1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()


# ─── ADD AD FSM ────────────────────────────────────────

@router.callback_query(F.data == "ad_add_start")
async def ad_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AddAdFSM.waiting_for_text)
    await callback.message.delete()
    await callback.message.answer(
        "📢 <b>Yangi reklama</b>\n\n"
        "1-qadam: Reklama matnini yuboring:\n"
        "(faqat rasm/video bo'lsa <code>-</code> yuboring)",
        parse_mode="HTML",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(AddAdFSM.waiting_for_text)
async def ad_get_text(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())
        return
    text = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(text=text)
    await state.set_state(AddAdFSM.waiting_for_media)
    await message.answer(
        "🎬 2-qadam: Reklama rasmi yoki videosini yuboring:\n"
        "(o'tkazib yuborish uchun ⏭ bosing)",
        reply_markup=skip_keyboard(),
    )


@router.message(AddAdFSM.waiting_for_media, F.photo)
async def ad_get_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(media_type="photo", media_file_id=message.photo[-1].file_id)
    await state.set_state(AddAdFSM.waiting_for_button_text)
    await message.answer(
        "🔗 3-qadam: Tugma matnini yuboring:\n"
        "(o'tkazib yuborish uchun ⏭ bosing)",
        reply_markup=skip_keyboard(),
    )


@router.message(AddAdFSM.waiting_for_media, F.video)
async def ad_get_video(message: Message, state: FSMContext) -> None:
    await state.update_data(media_type="video", media_file_id=message.video.file_id)
    await state.set_state(AddAdFSM.waiting_for_button_text)
    await message.answer(
        "🔗 3-qadam: Tugma matnini yuboring:\n"
        "(o'tkazib yuborish uchun ⏭ bosing)",
        reply_markup=skip_keyboard(),
    )


@router.message(AddAdFSM.waiting_for_media, F.text == "⏭ O'tkazib yuborish")
async def ad_skip_media(message: Message, state: FSMContext) -> None:
    await state.update_data(media_type=None, media_file_id=None)
    await state.set_state(AddAdFSM.waiting_for_button_text)
    await message.answer(
        "🔗 3-qadam: Tugma matnini yuboring:\n"
        "(o'tkazib yuborish uchun ⏭ bosing)",
        reply_markup=skip_keyboard(),
    )


@router.message(AddAdFSM.waiting_for_media, F.text != "❌ Bekor qilish")
async def ad_invalid_media(message: Message) -> None:
    await message.answer("⚠️ Rasm, video yuboring yoki ⏭ bosing!")


@router.message(AddAdFSM.waiting_for_button_text, F.text == "⏭ O'tkazib yuborish")
async def ad_skip_button_text(message: Message, state: FSMContext) -> None:
    await state.update_data(button_text=None, button_url=None)
    await state.set_state(AddAdFSM.waiting_for_duration)
    await message.answer(
        "📅 4-qadam: Reklama necha kun davomida chiqishi kerak?\n"
        "(masalan: 7, 30)",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddAdFSM.waiting_for_button_text, F.text != "❌ Bekor qilish")
async def ad_get_button_text(message: Message, state: FSMContext) -> None:
    await state.update_data(button_text=message.text.strip())
    await state.set_state(AddAdFSM.waiting_for_button_url)
    await message.answer(
        "🔗 5-qadam: Tugma URL sini yuboring:\n"
        "(https:// bilan boshlanishi kerak)",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddAdFSM.waiting_for_button_url, F.text != "❌ Bekor qilish")
async def ad_get_button_url(message: Message, state: FSMContext) -> None:
    url = message.text.strip()
    if not url.startswith("http"):
        await message.answer("⚠️ URL http(s):// bilan boshlanishi kerak!")
        return
    await state.update_data(button_url=url)
    await state.set_state(AddAdFSM.waiting_for_duration)
    await message.answer(
        "📅 6-qadam: Reklama necha kun davomida chiqishi kerak?\n"
        "(masalan: 7, 30)",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddAdFSM.waiting_for_duration, F.text != "❌ Bekor qilish")
async def ad_get_duration(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        days = int(message.text.strip())
        if days < 1:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Iltimos, musbat son yuboring (masalan: 7, 30)!")
        return

    data = await state.get_data()
    now = datetime.now()
    start_date = now
    end_date = now + timedelta(days=days)

    ad = await add_ad(
        session,
        text=data.get("text"),
        start_date=start_date,
        end_date=end_date,
        media_type=data.get("media_type"),
        media_file_id=data.get("media_file_id"),
        button_text=data.get("button_text"),
        button_url=data.get("button_url"),
    )

    await state.clear()

    await message.answer(
        f"✅ <b>Reklama qo'shildi!</b>\n\n"
        f"📅 Muddati: {days} kun\n"
        f"📅 Tugash sanasi: {end_date.strftime('%Y-%m-%d')}",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


# ─── DELETE / ACTIVATE ───────────────────────────────────

@router.callback_query(F.data.startswith("ad_delete_"))
async def ad_delete(callback: CallbackQuery, session: AsyncSession) -> None:
    ad_id = int(callback.data.split("_")[2])
    deleted = await delete_ad(session, ad_id)
    if deleted:
        await callback.answer("✅ O'chirildi!")
    else:
        await callback.answer("❌ Xatolik!", show_alert=True)
    await ads_menu(callback, session)


@router.callback_query(F.data.startswith("ad_deactivate_"))
async def ad_deactivate(callback: CallbackQuery, session: AsyncSession) -> None:
    ad_id = int(callback.data.split("_")[2])
    await update_ad(session, ad_id, is_active=False)
    await callback.answer("⛔️ O'chirildi!")
    await ad_detail(callback, session)


@router.callback_query(F.data.startswith("ad_activate_"))
async def ad_activate(callback: CallbackQuery, session: AsyncSession) -> None:
    ad_id = int(callback.data.split("_")[2])
    await update_ad(session, ad_id, is_active=True)
    await callback.answer("✅ Faollashtirildi!")
    await ad_detail(callback, session)


# ─── CANCEL ──────────────────────────────────────────────

@router.message(AddAdFSM.waiting_for_text, F.text == "❌ Bekor qilish")
@router.message(AddAdFSM.waiting_for_media, F.text == "❌ Bekor qilish")
@router.message(AddAdFSM.waiting_for_button_text, F.text == "❌ Bekor qilish")
@router.message(AddAdFSM.waiting_for_button_url, F.text == "❌ Bekor qilish")
@router.message(AddAdFSM.waiting_for_duration, F.text == "❌ Bekor qilish")
async def ad_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard())
