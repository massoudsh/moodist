"""اتصال دیتابیس — MVP با SQLite، در production با تغییر DATABASE_URL به PostgreSQL سوییچ می‌شود."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'wardrobe.db')}"
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
