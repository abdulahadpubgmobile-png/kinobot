from typing import Optional, List, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Series, Movie


async def add_series(
    session: AsyncSession,
    title: str,
    total_parts: int = 1,
    description: str = None,
    year: str = None,
    country: str = None,
    genre: str = None,
    poster_file_id: str = None,
) -> Series:
    series = Series(
        title=title,
        total_parts=total_parts,
        description=description,
        year=year,
        country=country,
        genre=genre,
        poster_file_id=poster_file_id,
    )
    session.add(series)
    await session.commit()
    await session.refresh(series)
    return series


async def get_series_by_id(session: AsyncSession, series_id: int) -> Optional[Series]:
    result = await session.execute(select(Series).where(Series.id == series_id))
    return result.scalar_one_or_none()


async def get_all_series(session: AsyncSession) -> List[Series]:
    result = await session.execute(select(Series).order_by(Series.created_at.desc()))
    return result.scalars().all()


async def get_series_with_parts(session: AsyncSession, series_id: int) -> Tuple[Optional[Series], List[Movie]]:
    series = await get_series_by_id(session, series_id)
    if not series:
        return None, []
    result = await session.execute(
        select(Movie).where(Movie.series_id == series_id).order_by(Movie.part_number)
    )
    parts = result.scalars().all()
    return series, parts


async def update_series(session: AsyncSession, series_id: int, **kwargs) -> Optional[Series]:
    series = await get_series_by_id(session, series_id)
    if not series:
        return None
    for key, value in kwargs.items():
        if hasattr(series, key) and value is not None:
            setattr(series, key, value)
    await session.commit()
    await session.refresh(series)
    return series


async def delete_series(session: AsyncSession, series_id: int) -> bool:
    series = await get_series_by_id(session, series_id)
    if series:
        await session.execute(
            update(Movie).where(Movie.series_id == series_id).values(series_id=None)
        )
        await session.delete(series)
        await session.commit()
        return True
    return False


async def get_movie_next_part(session: AsyncSession, movie_id: int) -> Optional[Movie]:
    """Berilgan kinoning keyingi qismini qaytaradi."""
    result = await session.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie or not movie.series_id:
        return None
    result = await session.execute(
        select(Movie).where(
            Movie.series_id == movie.series_id,
            Movie.part_number == movie.part_number + 1,
        )
    )
    return result.scalar_one_or_none()
