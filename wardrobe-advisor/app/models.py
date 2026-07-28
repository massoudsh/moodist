"""مدل‌های SQLAlchemy — مطابق مدل داده در docs/architecture.md"""

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    taste_profile: Mapped["TasteProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    wardrobe_items: Mapped[list["WardrobeItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class TasteProfile(Base):
    __tablename__ = "taste_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    preferred_colors: Mapped[list] = mapped_column(JSON, default=list)
    preferred_styles: Mapped[list] = mapped_column(JSON, default=list)
    budget_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    size: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship(back_populates="taste_profile")


class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    image_path: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    dominant_color: Mapped[str] = mapped_column(String)
    style: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    user: Mapped["User"] = relationship(back_populates="wardrobe_items")


class ProductQuery(Base):
    __tablename__ = "product_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    source_type: Mapped[str] = mapped_column(String)  # "image" | "url"
    source_value: Mapped[str] = mapped_column(String)
    extracted_category: Mapped[str] = mapped_column(String)
    extracted_color: Mapped[str] = mapped_column(String)
    extracted_style: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    recommendation: Mapped["Recommendation"] = relationship(
        back_populates="product_query", uselist=False, cascade="all, delete-orphan"
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_query_id: Mapped[int] = mapped_column(
        ForeignKey("product_queries.id"), unique=True
    )
    verdict: Mapped[str] = mapped_column(String)  # "buy" | "dont_buy"
    score: Mapped[float] = mapped_column(Float)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    product_query: Mapped["ProductQuery"] = relationship(back_populates="recommendation")


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_query_id: Mapped[int] = mapped_column(ForeignKey("product_queries.id"))
    decision: Mapped[str] = mapped_column(String)  # "bought" | "skipped"
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
