"""اسکیمای Pydantic برای ورودی/خروجی API"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    name: str
    email: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str


class TasteProfileIn(BaseModel):
    user_id: int
    preferred_colors: list[str] = []
    preferred_styles: list[str] = []
    budget_min: float | None = None
    budget_max: float | None = None
    size: str | None = None


class TasteProfileOut(TasteProfileIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class WardrobeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    category: str
    dominant_color: str
    style: str | None
    created_at: datetime


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_query_id: int
    verdict: str
    score: float
    reasons: list[str]
    extracted_category: str
    extracted_color: str


class PurchaseDecisionIn(BaseModel):
    user_id: int
    product_query_id: int
    decision: str  # "bought" | "skipped"
