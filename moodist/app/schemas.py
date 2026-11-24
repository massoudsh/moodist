"""اسکیمای Pydantic برای ورودی/خروجی API"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DECISION = Literal["bought", "skipped"]
OCCASION = Literal["casual", "formal", "sport"]
SEASON = Literal["winter", "spring", "summer", "autumn"]
ITEM_SEASON = Literal["winter", "spring", "summer", "autumn", "all"]


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
    season: str
    purchase_price: float | None
    times_worn: int
    archived: bool
    created_at: datetime


class WardrobeItemUpdateIn(BaseModel):
    category: str | None = None
    style: str | None = None
    season: ITEM_SEASON | None = None
    purchase_price: float | None = None


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


class WardrobeItemWearIn(BaseModel):
    times: int = Field(default=1, ge=1, le=50)


class ItemWearStatOut(BaseModel):
    item_id: int
    category: str
    dominant_color: str
    purchase_price: float | None
    times_worn: int
    cost_per_wear: float | None


class WearStatsOut(BaseModel):
    total_items: int
    tracked_items: int
    total_spend: float
    total_wears: int
    average_cost_per_wear: float | None
    best_value: list[ItemWearStatOut]
    least_worn: list[ItemWearStatOut]


class PackingPlanOut(BaseModel):
    days: int
    season: str | None
    items: list[OutfitItemOut]
    missing_categories: list[str]
    notes: list[str]


class SavedOutfitIn(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=80)
    occasion: OCCASION = "casual"
    item_ids: list[int] = Field(min_length=1, max_length=12)
    planned_for: datetime | None = None


class SavedOutfitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    name: str
    occasion: str
    item_ids: list[int]
    planned_for: datetime | None
    created_at: datetime
