"""فصل و شرایط آب‌وهوا برای پیشنهاد روزانهٔ لباس.

بدون فراخوانی سرویس خارجی: اگر دما و شرایط جوی از کلاینت بیاید استفاده می‌شود،
وگرنه فصل تقریبی از ماه میلادی و آب‌وهوای فلات ایران تخمین زده می‌شود.
"""

from dataclasses import dataclass
from datetime import date

SEASONS = ("winter", "spring", "summer", "autumn")

# آستانه‌های دمایی (°C) — از سردترین به گرم‌ترین
_TEMPERATURE_BANDS: tuple[tuple[float, str, str], ...] = (
    (8.0, "winter", "لایه‌های گرم و پوشش بیرونی لازم است"),
    (16.0, "autumn", "هوا خنک است؛ یک لایهٔ میانی یا کت سبک بپوش"),
    (25.0, "spring", "هوای معتدل است؛ چندلایهٔ سبک بهترین انتخاب است"),
    (float("inf"), "summer", "هوا گرم است؛ پارچهٔ نازک و رنگ روشن انتخاب کن"),
)


def season_for_month(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


@dataclass(frozen=True)
class Weather:
    season: str
    temperature_c: float | None
    condition: str
    advice: str


def weather_for(
    temperature_c: float | None = None,
    condition: str = "clear",
    today: date | None = None,
) -> Weather:
    condition = (condition or "clear").strip().lower()
    if temperature_c is not None:
        for threshold, season, advice in _TEMPERATURE_BANDS:
            if temperature_c < threshold:
                break
    else:
        season = season_for_month((today or date.today()).month)
        advice = next(
            text for _, name, text in _TEMPERATURE_BANDS if name == season
        )

    extra: list[str] = []
    if condition in ("rain", "drizzle", "storm"):
        extra.append("بارانی است؛ کفش ضدآب و لایهٔ ضدباران فراموش نشود")
    elif condition in ("snow", "sleet"):
        extra.append("برف/سرما است؛ کفش ضدآب و پوشش گرم لازم است")
    elif condition == "wind":
        extra.append("بادی است؛ لایهٔ ثابت و مانتو/کت بلند بهتر است")
    elif condition == "hot":
        extra.append("گرما شدید است؛ پارچهٔ نخی و رنگ روشن را ترجیح بده")

    return Weather(
        season=season,
        temperature_c=temperature_c,
        condition=condition,
        advice=" ".join([advice, *extra]),
    )
