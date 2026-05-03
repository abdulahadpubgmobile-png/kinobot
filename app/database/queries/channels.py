from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Channel


async def get_all_channels(session: AsyncSession) -> List[Channel]:
    result = await session.execute(select(Channel))
    return result.scalars().all()


async def add_channel(
    session: AsyncSession,
    channel_id: int,
    channel_link: str,
    channel_name: str,
) -> Channel:
    channel = Channel(
        channel_id=channel_id,
        channel_link=channel_link,
        channel_name=channel_name,
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return channel


async def remove_channel(session: AsyncSession, channel_id: int) -> bool:
    result = await session.execute(delete(Channel).where(Channel.channel_id == channel_id))
    await session.commit()
    return result.rowcount > 0
