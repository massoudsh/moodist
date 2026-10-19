"""تحلیل سبک کمد و پیشنهاد ست — منطق محلی بدون وابستگی به سرویس خارجی."""

from collections import Counter
from dataclasses import dataclass, field

from app.models import WardrobeItem
from app.vision import _NAMED_COLORS

CATEGORY_FAMILIES: dict[str, tuple[str, ...]] = {
    "top": ("shirt", "t-shirt", "blouse", "sweater", "hoodie", "top"),
    "bottom": ("pants", "jeans", "skirt", "shorts", "trousers"),
    "outerwear": ("jacket", "coat", "blazer"),
    "shoes": ("shoes", "sneakers", "boots"),
}

OCCASION_PRIORITIES: dict[str, tuple[str, ...]] = {
    "casual": ("top", "bottom", "shoes", "outerwear"),
    "formal": ("top", "bottom", "outerwear", "shoes"),
    "sport": ("top", "bottom", "shoes"),
}

MIN_CATEGORY_GAP = 90.0


def get_family(category: str) -> str | None:
    normalized = category.strip().lower()
    for family, categories in CATEGORY_FAMILIES.items():
        if normalized in categories:
            return family
    return None


def _rgb(color: str) -> tuple[int, int, int] | None:
    return _NAMED_COLORS.get(color)


def _color_distance(a: str, b: str) -> float | None:
    rgb_a, rgb_b = _rgb(a), _rgb(b)
    if rgb_a is None or rgb_b is None:
        return None
    return sum((x - y) ** 2 for x, y in zip(rgb_a, rgb_b)) ** 0.5


def _compatible(a: str, b: str) -> bool:
    distance = _color_distance(a, b)
    if distance is None:
        return True
    return distance >= MIN_CATEGORY_GAP


@dataclass
class WardrobeAnalysis:
    total_items: int
    categories: dict[str, int] = field(default_factory=dict)
    colors: dict[str, int] = field(default_factory=dict)
    dominant_colors: list[str] = field(default_factory=list)
    dominant_styles: list[str] = field(default_factory=list)
    missing_categories: list[str] = field(default_factory=list)


def analyze_wardrobe(wardrobe: list[WardrobeItem]) -> WardrobeAnalysis:
    categories = Counter(item.category for item in wardrobe)
    colors = Counter(item.dominant_color for item in wardrobe)
    styles = Counter(item.style for item in wardrobe if item.style)
    families_present = {get_family(item.category) for item in wardrobe}
    missing = [family for family in CATEGORY_FAMILIES if family not in families_present]
    return WardrobeAnalysis(
        total_items=len(wardrobe),
        categories=dict(categories),
        colors=dict(colors),
        dominant_colors=[name for name, _ in colors.most_common(3) if name != "unknown"],
        dominant_styles=[name for name, _ in styles.most_common(3).__iter__()],
        missing_categories=missing,
    )


@dataclass
class Outfit:
    occasion: str
    items: list[WardrobeItem]
    matched_color: str | None
    explanation: str


def suggest_outfits(
    wardrobe: list[WardrobeItem], occasion: str = "casual", limit: int = 3
) -> list[Outfit]:
    priorities = OCCASION_PRIORITIES.get(occasion)
    if priorities is None:
        raise ValueError(f"occasion نامعتبر: {occasion}")

    by_family: dict[str, list[WardrobeItem]] = {family: [] for family in CATEGORY_FAMILIES}
    for item in wardrobe:
        family = get_family(item.category)
        if family is not None:
            by_family[family].append(item)

    # محور ست: پوشاکی که بیشترین آیتم را دارد و در اولویت این موقعیت هست
    pivot = next(
        (family for family in priorities if by_family.get(family)),
        None,
    )
    if pivot is None:
        return []

    outfits: list[Outfit] = []
    for anchor in by_family[pivot][:limit]:
        chosen = [anchor]
        for family in priorities:
            if family == pivot or not by_family.get(family):
                continue
            compatible = [item for item in by_family[family] if _compatible(anchor.dominant_color, item.dominant_color)]
            choices = compatible or by_family[family]
            chosen.append(choices[0])
        outfits.append(
            Outfit(
                occasion=occasion,
                items=chosen,
                matched_color=anchor.dominant_color,
                explanation=f"ست {occasion} بر پایهٔ {anchor.category} {anchor.dominant_color}",
            )
        )
    return outfits


def style_advice(wardrobe: list[WardrobeItem], question: str) -> str:
    analysis = analyze_wardrobe(wardrobe)
    if not wardrobe:
        return "هنوز چیزی در کمدت ثبت نکرده‌ای؛ عکس لباس‌هایت را اضافه کن تا پیشنهاد شخصی بدهیم"

    lowered = question.strip().lower()
    if "رنگ" in question or "color" in lowered:
        colors = "، ".join(analysis.dominant_colors) or "متنوع"
        return f"رنگ‌های غالب کمدت {colors} است؛ می‌تونی ست‌های هم‌رنگ یا متضاد بچینی"
    if "تكرار" in question or "تکرار" in question or "repeat" in lowered:
        if analysis.categories:
            top = max(analysis.categories.items(), key=lambda entry: entry[1])
            return f"بیشترین تکرار را در دستهٔ {top[0]} داری ({top[1]} آیتم)"
        return "کمدت کافی متنوع است"
    if "کمبود" in question or "ناقص" in question or "missing" in lowered:
        if analysis.missing_categories:
            return "دسته‌های خالی کمدت: " + "، ".join(analysis.missing_categories)
        return "هیچ دستهٔ اصلی‌ای در کمدت خالی نیست"
    return (
        f"کمدت {analysis.total_items} آیتم در {len(analysis.categories)} دسته دارد و "
        "می‌تونی از «ست» یا تحلیل کمد استفاده کنی"
    )


def shopping_guidance(wardrobe: list[WardrobeItem]) -> list[str]:
    analysis = analyze_wardrobe(wardrobe)
    suggestions: list[str] = []
    for family in analysis.missing_categories:
        suggestions.append(f"یک {family} بخر که با رنگ‌های غالب کمدت ست شود")
    if analysis.dominant_colors:
        suggestions.append(
            f"آیتم بعدی را از پالت {analysis.dominant_colors[0]} انتخاب کن تا با کمدت هماهنگ باشد"
        )
    if not suggestions:
        suggestions.append("کمدت دسته‌های اصلی را پوشش داده؛ پیش از خرید، تکراری بودن را بسنج")
    return suggestions
