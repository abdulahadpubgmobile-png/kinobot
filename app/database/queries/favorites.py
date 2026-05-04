from typing import List, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Favorite, Movie


async def add_favorite(session: AsyncSession, user_id: int, movie_id: int) -> bool:
    existing = await session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.movie_id == movie_id)
    )
    if existing.scalar_one_or_none():
        return False
    fav = Favorite(user_id=user_id, movie_id=movie_id)
    session.add(fav)
    await session.commit()
    return True


async def remove_favorite(session: AsyncSession, user_id: int, movie_id: int) -> bool:
    result = await session.execute(
        delete(Favorite).where(Favorite.user_id == user_id, Favorite.movie_id == movie_id)
    )
    await session.commit()
    return result.rowcount > 0


async def is_favorite(session: AsyncSession, user_id: int, movie_id: int) -> bool:
    result = await session.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.movie_id == movie_id)
    )
    return result.scalar_one_or_none() is not None


async def get_user_favorites(session: AsyncSession, user_id: int) -> List[Movie]:
    result = await session.execute(
        select(Movie)
        .join(Favorite, Favorite.movie_id == Movie.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.added_at.desc())
    )
    return result.scalars().all()


async def get_users_by_genre(session: AsyncSession, genre: str) -> List[int]:
    """Berilgan janrli kinolarni sevimli qilgan foydalanuvchilar ID sini qaytaradi."""
    result = await session.execute(
        select(Favorite.user_id)
        .join(Movie, Movie.id == Favorite.movie_id)
        .where(Movie.genre.ilike(f"%{genre}%"))
        .distinct()
    )
    return [row[0] for row in result.fetchall()]
