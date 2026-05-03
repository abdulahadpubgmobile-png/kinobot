from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    fullname: str,
    username: Optional[str] = None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=telegram_id,
            fullname=fullname,
            username=username,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(fullname=fullname, username=username, last_activity=datetime.now())
        )
        await session.commit()

    return user


async def get_all_users(session: AsyncSession) -> List[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(User.id)))
    return result.scalar_one()
