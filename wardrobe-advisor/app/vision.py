"""تحلیل تصویر لباس.

`VisionAnalyzer` یک interface است تا در production بتوان آن را با یک مدل چندوجهی واقعی
(VLM) جایگزین کرد بدون تغییر در API یا مدل داده. `HeuristicVisionAnalyzer` پیاده‌سازی
MVP است: فقط رنگ غالب تصویر را با Pillow استخراج می‌کند (بدون فراخوانی مدل خارجی) و
دسته/سبک را از ورودی کاربر می‌گیرد.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO

from PIL import Image

# پالت رنگ‌های نام‌گذاری‌شده برای map کردن رنگ میانگین تصویر
_NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "red": (200, 30, 30),
    "orange": (230, 126, 34),
    "yellow": (241, 196, 15),
    "green": (39, 130, 60),
    "blue": (41, 91, 200),
    "navy": (20, 30, 80),
    "purple": (120, 50, 150),
    "pink": (230, 130, 170),
    "brown": (110, 70, 40),
    "beige": (222, 202, 168),
}


def _closest_color_name(rgb: tuple[int, int, int]) -> str:
    best_name, best_dist = "unknown", float("inf")
    for name, ref in _NAMED_COLORS.items():
        dist = sum((a - b) ** 2 for a, b in zip(rgb, ref))
        if dist < best_dist:
            best_name, best_dist = name, dist
    return best_name


@dataclass
class VisionResult:
    category: str
    dominant_color: str
    style: str | None = None


class VisionAnalyzer(ABC):
    @abstractmethod
    def analyze(self, image_bytes: bytes, category_hint: str) -> VisionResult: ...


class HeuristicVisionAnalyzer(VisionAnalyzer):
    """پیاده‌سازی MVP بدون وابستگی به سرویس خارجی.

    در production این کلاس با یک client مدل چندوجهی (مثلاً یک VLM که تصویر را می‌گیرد
    و category/style/pattern دقیق برمی‌گرداند) جایگزین می‌شود؛ امضای `analyze` باید
    یکسان بماند تا لایه‌های بالادست (main.py, matcher.py) بدون تغییر باقی بمانند.
    """

    def analyze(self, image_bytes: bytes, category_hint: str) -> VisionResult:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        image = image.resize((32, 32))  # سرعت — کافی برای تخمین رنگ غالب
        pixels = list(image.getdata())
        avg = tuple(sum(c[i] for c in pixels) // len(pixels) for i in range(3))
        color_name = _closest_color_name(avg)  # type: ignore[arg-type]
        return VisionResult(category=category_hint, dominant_color=color_name, style=None)
