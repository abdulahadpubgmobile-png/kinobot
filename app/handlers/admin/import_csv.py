import csv
import io
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.filters import IsAdmin
from app.database.queries.movies import add_movie, get_movie_by_code

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "admin_import_csv")
async def import_csv_start(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📥 <b>CSV bilan import</b>\n\n"
        "CSV fayl yuboring.\n\n"
        "Majburiy ustunlar: <code>code, title</code>\n"
        "Ixtiyoriy ustunlar: <code>year, country, genre, description, trailer_url, file_id, poster_file_id</code>\n\n"
        "Misol:\n"
        "<code>code,title,year,genre\n"
        "001,Inception,2010,Sci-Fi\n"
        "002,The Matrix,1999,Action</code>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(F.document)
async def handle_csv_upload(message: Message, session: AsyncSession) -> None:
    """CSV faylni qayta ishlash."""
    document = message.document
    if not document.file_name.endswith('.csv'):
        return  # Not a CSV file, ignore

    try:
        # Faylni yuklash
        file = await message.bot.get_file(document.file_id)
        file_content = await message.bot.download_file(file.file_path)

        # CSV ni o'qish
        csv_content = file_content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        success = 0
        failed = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # 1-qator header
            try:
                code = row.get('code', '').strip()
                title = row.get('title', '').strip()

                if not code or not title:
                    errors.append(f"Qator {row_num}: code yoki title yo'q")
                    failed += 1
                    continue

                # Kod mavjudligini tekshirish
                if await get_movie_by_code(session, code):
                    errors.append(f"Qator {row_num}: {code} kodi allaqachon mavjud")
                    failed += 1
                    continue

                # Kinoni qo'shish
                movie = await add_movie(
                    session,
                    code=code,
                    title=title,
                    year=row.get('year', '').strip() or None,
                    country=row.get('country', '').strip() or None,
                    genre=row.get('genre', '').strip() or None,
                    description=row.get('description', '').strip() or None,
                    trailer_url=row.get('trailer_url', '').strip() or None,
                    file_id=row.get('file_id', '').strip() or None,
                    poster_file_id=row.get('poster_file_id', '').strip() or None,
                )
                success += 1

            except Exception as e:
                errors.append(f"Qator {row_num}: {str(e)}")
                failed += 1

        # Natijalarni chiqarish
        result_text = f"📥 <b>Import natijasi</b>\n\n"
        result_text += f"✅ Muvaffaqiyatli: {success}\n"
        result_text += f"❌ Xatolar: {failed}\n\n"

        if errors and len(errors) <= 10:
            result_text += "Xatolar:\n" + "\n".join(errors[:10])
        elif errors:
            result_text += f"Dastlabki 10 ta xato ko'rsatilmoqda:\n" + "\n".join(errors[:10])

        await message.answer(result_text, parse_mode="HTML", reply_markup=main_keyboard())

    except Exception as e:
        await message.answer(
            f"❌ <b>Xatolik yuz berdi:</b>\n{str(e)}",
            parse_mode="HTML",
        )


def main_keyboard():
    from app.keyboards.reply import main_keyboard as mk
    return mk()
