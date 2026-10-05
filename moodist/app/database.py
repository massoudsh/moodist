"""اتصال دیتابیس — SQLite برای توسعه/تست، PostgreSQL در production (از طریق MOODIST_DATABASE_URL)."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = config.DATABASE_URL or f"sqlite:///{os.path.join(BASE_DIR, 'moodist.db')}"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # سنجش سلامت اتصال پیش از استفاده (مهم برای PostgreSQL تولیدی)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
