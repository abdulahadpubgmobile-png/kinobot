from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Ad


async def add_ad(
    session: AsyncSession,
    text: str,
    start_date: datetime,
    end_date: datetime,
    media_type: str = None,
    media_file_id: str = None,
    button_text: str = None,
    button_url: str = None,
) -> Ad:
    ad = Ad(
        text=text,
        media_type=media_type,
        media_file_id=media_file_id,
        button_text=button_text,
        button_url=button_url,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
    )
    session.add(ad)
    await session.commit()
    await session.refresh(ad)
    return ad


async def get_active_ads(session: AsyncSession) -> List[Ad]:
    now = datetime.now()
    result = await session.execute(
        select(Ad).where(
            Ad.is_active == True,
            Ad.start_date <= now,
            Ad.end_date >= now,
        )
    )
    return result.scalars().all()


async def get_all_ads(session: AsyncSession) -> List[Ad]:
    result = await session.execute(select(Ad).order_by(Ad.created_at.desc()))
    return result.scalars().all()


async def get_ad_by_id(session: AsyncSession, ad_id: int) -> Optional[Ad]:
    result = await session.execute(select(Ad).where(Ad.id == ad_id))
    return result.scalar_one_or_none()


async def update_ad(session: AsyncSession, ad_id: int, **kwargs) -> Optional[Ad]:
    ad = await get_ad_by_id(session, ad_id)
    if not ad:
        return None
    for key, value in kwargs.items():
        if hasattr(ad, key) and value is not None:
            setattr(ad, key, value)
    await session.commit()
    await session.refresh(ad)
    return ad


async def delete_ad(session: AsyncSession, ad_id: int) -> bool:
    ad = await get_ad_by_id(session, ad_id)
    if ad:
        await session.delete(ad)
        await session.commit()
        return True
    return False


async def deactivate_expired_ads(session: AsyncSession) -> int:
    now = datetime.now()
    result = await session.execute(
        update(Ad)
        .where(Ad.is_active == True, Ad.end_date < now)
        .values(is_active=False)
    )
    await session.commit()
    return result.rowcount
