"""موتور تصمیم بخر/نخر — امتیازدهی بر اساس شباهت به کمد + تطابق سلیقه + بودجه."""

from dataclasses import dataclass, field

from app.models import TasteProfile, WardrobeItem
from app.vision import VisionResult

SIMILARITY_PENALTY_PER_ITEM = 0.15
MAX_SIMILARITY_PENALTY = 0.45
COLOR_MATCH_BONUS = 0.3
COLOR_MISMATCH_PENALTY = 0.1
BUDGET_FIT_BONUS = 0.15
BUDGET_MISS_PENALTY = 0.25
BUY_THRESHOLD = 0.5


@dataclass
class Decision:
    verdict: str  # "buy" | "dont_buy"
    score: float
    reasons: list[str] = field(default_factory=list)


def decide(
    vision: VisionResult,
    wardrobe: list[WardrobeItem],
    taste: TasteProfile | None,
    price: float | None = None,
) -> Decision:
    score = 0.5
    reasons: list[str] = []

    # شباهت به آیتم‌های موجود در کمد (همان دسته + همان رنگ = تکراری)
    similar = [
        item
        for item in wardrobe
        if item.category == vision.category and item.dominant_color == vision.dominant_color
    ]
    if similar:
        penalty = min(len(similar) * SIMILARITY_PENALTY_PER_ITEM, MAX_SIMILARITY_PENALTY)
        score -= penalty
        reasons.append(
            f"{len(similar)} آیتم مشابه ({vision.dominant_color}, {vision.category}) در کمدت داری"
        )
    else:
        reasons.append(f"هیچ آیتم {vision.dominant_color} {vision.category} مشابهی در کمدت نیست")

    # تطابق با رنگ‌های موردعلاقه
    preferred_colors = taste.preferred_colors if taste else []
    if preferred_colors:
        if vision.dominant_color in preferred_colors:
            score += COLOR_MATCH_BONUS
            reasons.append(f"رنگ {vision.dominant_color} جزو رنگ‌های موردعلاقه‌ات است")
        else:
            score -= COLOR_MISMATCH_PENALTY
            reasons.append(f"رنگ {vision.dominant_color} در لیست رنگ‌های موردعلاقه‌ات نیست")

    # تناسب با بودجه (در صورت ارسال قیمت)
    if price is not None and taste is not None and (
        taste.budget_min is not None or taste.budget_max is not None
    ):
        lo = taste.budget_min if taste.budget_min is not None else 0
        hi = taste.budget_max if taste.budget_max is not None else float("inf")
        if lo <= price <= hi:
            score += BUDGET_FIT_BONUS
            reasons.append("قیمت داخل بودجهٔ تعیین‌شدهٔ توست")
        else:
            score -= BUDGET_MISS_PENALTY
            reasons.append("قیمت خارج از بودجهٔ تعیین‌شدهٔ توست")

    score = max(0.0, min(1.0, score))
    verdict = "buy" if score >= BUY_THRESHOLD else "dont_buy"
    return Decision(verdict=verdict, score=round(score, 3), reasons=reasons)
