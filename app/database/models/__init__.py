from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime,
    ForeignKey, Integer, String, Text, func,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    fullname = Column(String(255), nullable=True)
    username = Column(String(100), nullable=True)
    joined_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User id={self.id} telegram_id={self.telegram_id}>"


class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    series_id = Column(Integer, nullable=True)  # Agar kino serial qismi bo'lsa
    part_number = Column(Integer, default=1)  # Qaysi qism (1, 2, 3...)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    year = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)
    genre = Column(String(100), nullable=True)
    file_id = Column(String(500), nullable=True)
    poster_file_id = Column(String(500), nullable=True)
    trailer_url = Column(String(500), nullable=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Movie code={self.code} title={self.title}>"


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    channel_id = Column(BigInteger, unique=True, nullable=False)
    channel_link = Column(String(255), nullable=False)
    channel_name = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Channel name={self.channel_name}>"


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    movie_id = Column(Integer, nullable=False)
    added_at = Column(DateTime, default=func.now())


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    movie_id = Column(Integer, nullable=False)
    watched_at = Column(DateTime, default=func.now())


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    movie_id = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=True)
    media_type = Column(String(10), nullable=True)  # photo, video, or None
    media_file_id = Column(String(500), nullable=True)
    button_text = Column(String(100), nullable=True)
    button_url = Column(String(500), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class Series(Base):
    __tablename__ = "series"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    year = Column(String(10), nullable=True)
    country = Column(String(100), nullable=True)
    genre = Column(String(100), nullable=True)
    total_parts = Column(Integer, default=1)
    poster_file_id = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
