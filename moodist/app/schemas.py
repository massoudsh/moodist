"""اسکیمای Pydantic برای ورودی/خروجی API"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

DECISION = Literal["bought", "skipped"]
OCCASION = Literal["casual", "formal", "sport"]


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
    decision: DECISION


class WardrobeAnalysisOut(BaseModel):
    total_items: int
    categories: dict[str, int]
    colors: dict[str, int]
    dominant_colors: list[str]
    dominant_styles: list[str]
    missing_categories: list[str]


class OutfitItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    category: str
    dominant_color: str


class OutfitOut(BaseModel):
    occasion: OCCASION
    items: list[OutfitItemOut]
    matched_color: str | None
    explanation: str


class StyleQuestionIn(BaseModel):
    user_id: int
    question: str
