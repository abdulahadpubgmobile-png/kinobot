from typing import Optional, List, Tuple
from sqlalchemy import select, func, update, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Movie

MOVIES_PER_PAGE = 5


async def add_movie(session: AsyncSession, **kwargs) -> Movie:
    movie = Movie(**kwargs)
    session.add(movie)
    await session.commit()
    await session.refresh(movie)
    return movie


async def get_movie_by_code(session: AsyncSession, code: str) -> Optional[Movie]:
    result = await session.execute(select(Movie).where(Movie.code == code))
    return result.scalar_one_or_none()


async def get_movie_by_id(session: AsyncSession, movie_id: int) -> Optional[Movie]:
    result = await session.execute(select(Movie).where(Movie.id == movie_id))
    return result.scalar_one_or_none()


async def search_movies(
    session: AsyncSession,
    query: str,
    page: int = 1,
) -> Tuple[List[Movie], int]:
    base_q = select(Movie).where(
        or_(
            Movie.title.ilike(f"%{query}%"),
            Movie.code == query,
        )
    )
    count_result = await session.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * MOVIES_PER_PAGE
    result = await session.execute(base_q.offset(offset).limit(MOVIES_PER_PAGE))
    movies = result.scalars().all()

    return movies, total


async def get_movies_by_genre(
    session: AsyncSession,
    genre: str,
    page: int = 1,
) -> Tuple[List[Movie], int]:
    base_q = select(Movie).where(Movie.genre.ilike(f"%{genre}%"))
    count_result = await session.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_result.scalar_one()

    offset = (page - 1) * MOVIES_PER_PAGE
    result = await session.execute(base_q.offset(offset).limit(MOVIES_PER_PAGE))
    movies = result.scalars().all()

    return movies, total


async def get_all_movies(
    session: AsyncSession,
    page: int = 1,
) -> Tuple[List[Movie], int]:
    base_q = select(Movie).order_by(Movie.created_at.desc())
    count_result = await session.execute(select(func.count(Movie.id)))
    total = count_result.scalar_one()

    offset = (page - 1) * MOVIES_PER_PAGE
    result = await session.execute(base_q.offset(offset).limit(MOVIES_PER_PAGE))
    movies = result.scalars().all()

    return movies, total


async def increment_views(session: AsyncSession, movie_id: int) -> None:
    await session.execute(
        update(Movie).where(Movie.id == movie_id).values(views=Movie.views + 1)
    )
    await session.commit()


async def count_movies(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(Movie.id)))
    return result.scalar_one()


async def total_views(session: AsyncSession) -> int:
    result = await session.execute(select(func.sum(Movie.views)))
    return result.scalar_one() or 0


async def delete_movie(session: AsyncSession, movie_id: int) -> bool:
    movie = await get_movie_by_id(session, movie_id)
    if movie:
        await session.delete(movie)
        await session.commit()
        return True
    return False


async def update_movie(session: AsyncSession, movie_id: int, **kwargs) -> Optional[Movie]:
    movie = await get_movie_by_id(session, movie_id)
    if not movie:
        return None
    for key, value in kwargs.items():
        if hasattr(movie, key) and value is not None:
            setattr(movie, key, value)
    await session.commit()
    await session.refresh(movie)
    return movie


async def get_all_genres(session: AsyncSession) -> List[str]:
    result = await session.execute(select(Movie.genre).distinct())
    genres = [row[0] for row in result.fetchall() if row[0]]
    return genres
