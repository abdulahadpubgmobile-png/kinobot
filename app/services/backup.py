import logging
import subprocess
from datetime import datetime


async def backup_database(bot, admin_id: int) -> None:
    """
    Har kuni bir marta adminning Telegram ga
    backup faylini yuboradi.
    """
    try:
        date = datetime.now().strftime("%Y-%m-%d")
        filename = f"backup_{date}.sql"

        # pg_dump orqali backup olish
        db_url = "postgresql://abdulahad_gofurjonov_user:****@.../abdulahad_gofurjonov"

        result = subprocess.run(
            ["pg_dump", db_url, "-f", filename],
            capture_output=True,
        )

        if result.returncode == 0:
            with open(filename, "rb") as f:
                await bot.send_document(
                    chat_id=admin_id,
                    document=f,
                    caption=f"✅ Backup {date}",
                )
    except Exception as e:
        logging.error(f"Backup xatosi: {e}")