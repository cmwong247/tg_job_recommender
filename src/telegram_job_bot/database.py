"""Database session and models."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from .config import Settings


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=False)
    tg_username = Column(String(255), nullable=True)
    prefs_json = Column(Text, nullable=False, default="{}")
    notification_time = Column(String(5), nullable=False, default="09:00")
    timezone = Column(String(64), nullable=False, default="Asia/Singapore")
    next_digest_at = Column(DateTime, nullable=True)

    keywords = relationship("UserKeyword", back_populates="user", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")


class UserKeyword(Base):
    __tablename__ = "user_keywords"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    keyword = Column(String(255), nullable=False)
    weight = Column(Float, nullable=False, default=0.0)
    is_negative = Column(Boolean, nullable=False, default=False)
    rationale = Column(Text, nullable=True)

    user = relationship("User", back_populates="keywords")


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String(255), primary_key=True)
    title = Column(String(512), nullable=False)
    company = Column(String(255), nullable=True)
    loc = Column(String(255), nullable=True)
    desc = Column(Text, nullable=True)
    url = Column(String(1024), nullable=True)
    posted_at = Column(DateTime, nullable=True)

    interactions = relationship("Interaction", back_populates="job", cascade="all, delete-orphan")


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    job_id = Column(String(255), ForeignKey("jobs.job_id"), nullable=False)
    action = Column(String(16), nullable=False)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    job = relationship("Job", back_populates="interactions")


def create_session_factory(settings: Settings):
    engine = create_engine(settings.database_url, future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope(SessionFactory) -> Generator:
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def upsert_user(session, user_id: int, username: Optional[str] = None) -> User:
    user = session.get(User, user_id)
    if user is None:
        user = User(user_id=user_id, tg_username=username)
        session.add(user)
    else:
        if username and user.tg_username != username:
            user.tg_username = username
    return user
