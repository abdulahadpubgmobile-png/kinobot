# ✅ TO'LIQ YANGI KOD:
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import config
from app.database.models import Base


def get_engine():
    db_url = config.db_url

    # PostgreSQL uchun pool sozlamalari
    if db_url.startswith("postgresql"):
        return create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    # SQLite uchun (lokal test)
    else:
        return create_async_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
        )


engine = get_engine()

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
