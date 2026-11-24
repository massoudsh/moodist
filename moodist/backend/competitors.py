from datetime import date

_UPDATED = date(2026, 11, 24).isoformat()

IRAN_COMPETITORS = [
    {
        "name": "جالباسی",
        "type": "direct",
        "features": [
            "کمد دیجیتال و دسته‌بندی خودکار",
            "پیشنهاد ست با هوش مصنوعی",
            "پیشنهاد بر اساس فصل و مناسبت",
            "هماهنگی رنگ",
            "اشتراک‌گذاری استایل و شبکه اجتماعی",
        ],
        "moodist_response": "فصل‌بندی کمد و پیشنهاد روز متناسب با آب‌وهوا اضافه شد",
        "source": "https://jalebasy.com/",
    },
    {
        "name": "چی‌بپوشم",
        "type": "direct",
        "features": [
            "استایل شخصی و تحلیل فرم بدن",
            "کمد دیجیتال و پیشنهاد روزانه",
            "پرو مجازی",
            "اتصال پیشنهاد به فروشگاه و قیمت",
            "API و افزونه وردپرس برای فروشگاه‌ها",
        ],
        "moodist_response": "پیشنهاد روز و فهرست سفر اضافه شد؛ اتصال فروشگاهی در نقشه راه است",
        "source": "https://chibepoosham.app/",
    },
    {
        "name": "MiriYou",
        "type": "direct",
        "features": [
            "پرو مجازی با عکس کاربر یا اسکرین‌شات محصول",
            "کمد مجازی",
            "فید خرید با قیمت و لینک",
            "هشدار کاهش قیمت",
            "پروفایل خانوادگی",
        ],
        "moodist_response": "قیمت خرید هر آیتم و هزینهٔ هر بار استفاده ثبت می‌شود",
        "source": "https://miriyou.com/fa",
    },
    {
        "name": "Doku",
        "type": "direct",
        "features": [
            "کمد دیجیتال",
            "استایلیست هوش مصنوعی و برنامه‌ریزی سفر",
            "آینه واقعیت افزوده",
            "رقابت اجتماعی استایل",
        ],
        "moodist_response": "فهرست بسته‌بندی سفر و برنامه‌ریزی ست اضافه شد",
        "source": "https://doku.style/fa",
    },
    {
        "name": "ModAI",
        "type": "direct",
        "features": [
            "بازار تجمیعی چند فروشگاه",
            "جست‌وجوی متنی و تصویری",
            "پیشنهاد آیتم‌های مکمل",
            "پرو مجازی و پشتیبانی/تضمین خرید",
        ],
        "moodist_response": "پیشنهاد مکمل و ست با کمد موجود؛ اتصال کاتالوگ در نقشه راه است",
        "source": "https://modai.fashion/",
    },
]

INTERNATIONAL_COMPETITORS = [
    {
        "name": "Whering",
        "features": [
            "کمد دیجیتال با حذف پس‌زمینه",
            "هزینهٔ هر بار استفاده و آمار پوشیدن",
            "برنامه‌ریز و پیشنهاد بر پایهٔ هوا",
            "فهرست بسته‌بندی سفر",
            "کمد دوستان و استایل دادن به دیگران",
        ],
        "source": "https://whering.co.uk/",
    },
    {
        "name": "Acloset",
        "features": [
            "پیشنهاد روزانهٔ مبتنی بر آب‌وهوا",
            "استایلیست چت‌محور",
            "تقویم و برنامه‌ریزی ست",
            "آمار پوشیدن و هزینهٔ هر بار استفاده",
            "فید اجتماعی استایل",
        ],
        "source": "https://www.acloset.co/",
    },
    {
        "name": "Stylebook",
        "features": [
            "تقویم ست و برنامه‌ریزی روزانه",
            "فهرست بسته‌بندی سفر",
            "آمار سبک و هزینهٔ هر بار استفاده",
            "بوم آزاد برای چیدن ست",
            "پرچم وضعیت آیتم (تعمیر/اهدا)",
        ],
        "source": "https://www.stylebookapp.com/",
    },
    {
        "name": "Cladwell",
        "features": [
            "کپسول فصلی حدود ۳۳ قطعه",
            "فرمول ست و نقش رنگ",
            "استایلیست چت و تحلیل رنگ",
            "پیشنهاد روزانه",
            "فهرست خرید بر پایهٔ شکاف کمد",
        ],
        "source": "https://cladwell.com/",
    },
    {
        "name": "Alta",
        "features": [
            "پیشنهاد ست و استایلیست چت",
            "فهرست بسته‌بندی سفر",
            "هزینهٔ هر بار استفاده",
            "آواتار و رندر پوشیدنی",
            "پیشنهاد خرید بر پایهٔ شکاف کمد",
        ],
        "source": "https://alta.co/",
    },
]

# پنج قابلیتی که از رقبا استخراج و در مودیست پیاده شد.
IMPLEMENTED_FEATURES = [
    {
        "feature": "فصل‌بندی کمد و پیشنهاد روز مبتنی بر آب‌وهوا",
        "endpoint": "GET /outfits/today/{user_id}",
        "sources": ["جالباسی", "Whering", "Acloset", "Stylebook"],
    },
    {
        "feature": "ردیابی پوشیدن و هزینهٔ هر بار استفاده",
        "endpoint": "POST /wardrobe/{item_id}/wear · GET /wardrobe/stats/{user_id}",
        "sources": ["Whering", "Stylebook", "Acloset", "MiriYou"],
    },
    {
        "feature": "فهرست بسته‌بندی سفر",
        "endpoint": "GET /packing-plan/{user_id}",
        "sources": ["Stylebook", "Whering", "Alta", "Doku"],
    },
    {
        "feature": "ذخیره و برنامه‌ریزی ست (کپسول شخصی)",
        "endpoint": "POST /outfits/saved · GET /outfits/saved/{user_id}",
        "sources": ["Stylebook", "Acloset", "Cladwell", "Doku"],
    },
    {
        "feature": "ویرایش/بایگانی آیتم کمد و قیمت خرید",
        "endpoint": "PATCH /wardrobe/{item_id} · DELETE /wardrobe/{item_id}",
        "sources": ["Whering", "Acloset", "MiriYou", "ModAI"],
    },
]

COMPETITOR_REPORT = {
    "market": "fashion-ai-wardrobe",
    "updated_at": _UPDATED,
    "competitors": IRAN_COMPETITORS,
    "international": INTERNATIONAL_COMPETITORS,
    "implemented_features": IMPLEMENTED_FEATURES,
}


def get_competitor_report() -> dict:
    return COMPETITOR_REPORT


def get_iran_competitor_report() -> dict:
    return {
        "market": "iran-fashion-ai",
        "updated_at": _UPDATED,
        "competitors": IRAN_COMPETITORS,
    }
