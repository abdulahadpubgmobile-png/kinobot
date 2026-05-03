from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import WatchHistory, Movie


async def add_watch_history(session: AsyncSession, user_id: int, movie_id: int) -> None:
    history = WatchHistory(user_id=user_id, movie_id=movie_id)
    session.add(history)
    await session.commit()


async def get_user_history(session: AsyncSession, user_id: int, limit: int = 10) -> list:
    result = await session.execute(
        select(Movie)
        .join(WatchHistory, WatchHistory.movie_id == Movie.id)
        .where(WatchHistory.user_id == user_id)
        .order_by(WatchHistory.watched_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
