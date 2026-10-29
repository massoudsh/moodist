from datetime import date

COMPETITOR_REPORT = {
    "market": "iran-fashion-ai",
    "updated_at": date(2026, 10, 29).isoformat(),
    "competitors": [
        {
            "name": "جالباسی",
            "type": "direct",
            "features": [
                "کمد دیجیتال و دسته‌بندی لباس",
                "پیشنهاد ست با هوش مصنوعی",
                "پیشنهاد بر اساس فصل و مناسبت",
                "هماهنگی رنگ",
                "اشتراک‌گذاری استایل و شبکه اجتماعی",
            ],
            "moodist_response": "افزودن مناسبت/فصل و اشتراک‌گذاری استایل به نقشه راه",
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
            "moodist_response": "اولویت دادن به اتصال فروشگاهی، سایزبندی و پرو مجازی پس از زیرساخت تولید",
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
                "پروفایل خانوادگی و حفظ حریم خصوصی",
            ],
            "moodist_response": "افزودن watchlist و هشدار قیمت بعد از اتصال کاتالوگ فروشگاه‌ها",
            "source": "https://miriyou.com/fa",
        },
        {
            "name": "Doku",
            "type": "direct",
            "features": [
                "کمد دیجیتال",
                "استایلیست هوش مصنوعی و برنامه‌ریزی سفر",
                "آینه واقعیت افزوده",
                "رقابت و رأی‌گیری اجتماعی استایل",
            ],
            "moodist_response": "افزودن برنامه‌ریزی سفر و رأی‌گیری اجتماعی به فاز رشد، نه MVP تولیدی",
            "source": "https://doku.style/fa",
        },
        {
            "name": "ModAI",
            "type": "direct",
            "features": [
                "بازار تجمیعی چند فروشگاه",
                "جست‌وجوی متنی و تصویری",
                "پیشنهاد آیتم‌های مکمل",
                "پرو مجازی و پشتیبانی خرید",
            ],
            "moodist_response": "تکمیل جست‌وجوی محصول و پیشنهاد مکمل با کاتالوگ فروشگاه‌های ایرانی",
            "source": "https://ir.linkedin.com/company/modai-app",
        },
    ],
}


def get_competitor_report() -> dict:
    return COMPETITOR_REPORT
