import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.database.queries.movies import add_movie, get_movie_by_code
from app.keyboards.inline import admin_panel_keyboard, back_keyboard
from app.keyboards.reply import main_keyboard

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "admin_import")
async def import_menu(callback: CallbackQuery) -> None:
    text = (
        "📥 <b>JSON orqali kino qo'shish</b>\n\n"
        "Quyidagi formatda JSON fayl yuboring:\n"
        "<code>[\n"
        '  {"code": "001", "title": "Kino nomi", "year": "2024",\n'
        '   "genre": "Action", "file_id": "FILE_ID"}\n'
        "]</code>\n\n"
        "📄 Shablon uchun /template yuklab oling."
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_keyboard("back_admin"))
    await callback.answer()


@router.message(F.document.mime_type == "application/json")
async def handle_json_import(message: Message, session: AsyncSession) -> None:
    # JSON faylni yuklab olish
    file = await message.bot.get_file(message.document.file_id)
    file_content = await message.bot.download_file(file.file_path)
    content = file_content.read()

    try:
        data = json.loads(content)
        if not isinstance(data, list):
            await message.answer("❌ JSON fayl ro'yxat (array) bo'lishi kerak!")
            return
    except json.JSONDecodeError:
        await message.answer("❌ JSON fayl noto'g'ri formatda!")
        return

    added = 0
    skipped = 0
    errors = []

    for item in data:
        try:
            code = str(item.get("code", "")).strip()
            title = str(item.get("title", "")).strip()

            if not code or not title:
                skipped += 1
                continue

            if await get_movie_by_code(session, code):
                skipped += 1
                continue

            file_id = str(item.get("file_id", "")).strip() or None
            poster_file_id = str(item.get("poster_file_id", "")).strip() or None

            await add_movie(
                session,
                code=code,
                title=title,
                year=str(item.get("year", "")) or None,
                country=str(item.get("country", "")) or None,
                genre=str(item.get("genre", "")) or None,
                description=str(item.get("description", "")) or None,
                trailer_url=str(item.get("trailer_url", "")) or None,
                file_id=file_id,
                poster_file_id=poster_file_id,
            )
            added += 1
        except Exception as e:
            errors.append(f"{item.get('code', '?')}: {e}")

    result_text = (
        f"✅ <b>Import yakunlandi!</b>\n\n"
        f"➕ Qo'shildi: {added}\n"
        f"⏭ O'tkazib yuborildi: {skipped}\n"
    )
    if errors:
        result_text += f"\n❌ Xatolar ({len(errors)}):\n" + "\n".join(errors[:5])

    await message.answer(result_text, parse_mode="HTML", reply_markup=main_keyboard())


@router.message(F.text == "/template")
async def send_template(message: Message) -> None:
    import os
    template_path = "movies_template.json"
    if os.path.exists(template_path):
        await message.answer_document(
            document=open(template_path, "rb"),
            caption="📄 Mana shablon fayli. Uni to'ldirib, botga yuboring.",
        )
    else:
        await message.answer("❌ Shablon fayli topilmadi.")
