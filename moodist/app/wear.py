"""ردیابی پوشیدن و محاسبهٔ هزینهٔ هر بار استفاده (cost per wear)."""

from dataclasses import dataclass, field

from app.models import WardrobeItem


def cost_per_wear(price: float | None, times_worn: int) -> float | None:
    if price is None:
        return None
    return round(price / max(times_worn, 1), 2)


@dataclass
class ItemWearStat:
    item_id: int
    category: str
    dominant_color: str
    purchase_price: float | None
    times_worn: int
    cost_per_wear: float | None


@dataclass
class WearStats:
    total_items: int
    tracked_items: int
    total_spend: float
    total_wears: int
    average_cost_per_wear: float | None
    best_value: list[ItemWearStat] = field(default_factory=list)
    least_worn: list[ItemWearStat] = field(default_factory=list)


def wardrobe_stats(wardrobe: list[WardrobeItem]) -> WearStats:
    stats = [
        ItemWearStat(
            item_id=item.id,
            category=item.category,
            dominant_color=item.dominant_color,
            purchase_price=item.purchase_price,
            times_worn=item.times_worn or 0,
            cost_per_wear=cost_per_wear(item.purchase_price, item.times_worn or 0),
        )
        for item in wardrobe
    ]
    priced = [stat for stat in stats if stat.purchase_price is not None]
    with_cpw = [stat for stat in priced if stat.cost_per_wear is not None]
    best = sorted(with_cpw, key=lambda stat: stat.cost_per_wear)[:3]
    least = sorted(
        (stat for stat in stats if stat.times_worn == 0),
        key=lambda stat: stat.purchase_price or 0,
        reverse=True,
    )[:3]
    average = (
        round(sum(stat.cost_per_wear for stat in with_cpw) / len(with_cpw), 2)
        if with_cpw
        else None
    )
    return WearStats(
        total_items=len(wardrobe),
        tracked_items=len(priced),
        total_spend=round(sum(stat.purchase_price for stat in priced), 2),
        total_wears=sum(stat.times_worn for stat in stats),
        average_cost_per_wear=average,
        best_value=best,
        least_worn=least,
    )
