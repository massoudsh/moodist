PAGES = {
    "home": {
        "path": "/",
        "title": "مودیست",
        "description": "دستیار هوشمند تصمیم‌گیری و ست‌سازی پوشاک",
        "actions": ["analyze", "outfits", "wardrobe"],
    },
    "wardrobe": {
        "path": "/wardrobe",
        "title": "کمد من",
        "description": "مدیریت کمد دیجیتال و تحلیل رنگ و دسته‌بندی",
        "actions": ["wardrobe_analysis", "shopping_guidance", "add_item"],
    },
    "outfits": {
        "path": "/outfits",
        "title": "پیشنهاد ست",
        "description": "ساخت ست بر اساس کمد، مناسبت و رنگ‌های هماهنگ",
        "actions": ["suggest_outfits", "style_advice"],
    },
    "discover": {
        "path": "/discover",
        "title": "کشف محصول",
        "description": "تحلیل محصول و آماده‌سازی اتصال به فروشگاه‌های ایرانی",
        "actions": ["analyze", "shopping_guidance"],
    },
    "profile": {
        "path": "/profile",
        "title": "پروفایل استایل",
        "description": "سلیقه، بودجه و سایز کاربر",
        "actions": ["taste_profile", "style_advice"],
    },
}


def page_list() -> list[dict]:
    return list(PAGES.values())


def get_page(slug: str) -> dict | None:
    return PAGES.get(slug)
