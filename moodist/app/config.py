"""پیکربندی متمرکز از طریق متغیرهای محیطی.

در محیط production (``ENV=production``) مقادیر ناامنِ پیش‌فرض رد می‌شوند و راه‌اندازی
با خطای واضح متوقف می‌شود، مگر اینکه configuration درست تأمین شده باشد:
``ENV``, ``MOODIST_SECRET_KEY``, ``DATABASE_URL`` (PostgreSQL), ``VISION_PROVIDER=llm``,
``S3_BUCKET`` و اعتبارنامه‌های S3.
"""

import os


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


ENV = env("MOODIST_ENV", "development").lower()
IS_PRODUCTION = ENV == "production"

# احراز هویت — در production باید صریحاً مقداردهی شود.
SECRET_KEY = env("MOODIST_SECRET_KEY", "dev-insecure-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_SECONDS = int(env("MOODIST_TOKEN_TTL", "86400"))

# دیتابیس — در production باید PostgreSQL باشد (SQLite فقط توسعه/تست).
DATABASE_URL = env("MOODIST_DATABASE_URL", "")

# تحلیل تصویر — ``heuristic`` فقط برای توسعه/تست؛ production باید ``llm`` باشد.
VISION_PROVIDER = env("MOODIST_VISION_PROVIDER", "heuristic")
LLM_API_URL = env("MOODIST_LLM_API_URL", "")
LLM_API_KEY = env("MOODIST_LLM_API_KEY", "")
LLM_MODEL = env("MOODIST_LLM_MODEL", "")
VISION_TIMEOUT_SECONDS = float(env("MOODIST_VISION_TIMEOUT", "20"))

# ذخیره‌سازی تصویر — ``local`` فقط توسعه؛ production باید ``s3`` باشد.
STORAGE_BACKEND = env("MOODIST_STORAGE_BACKEND", "local")
S3_BUCKET = env("MOODIST_S3_BUCKET", "")
S3_PREFIX = env("MOODIST_S3_PREFIX", "moodist/images")
S3_ENDPOINT_URL = env("MOODIST_S3_ENDPOINT_URL", "") or None
S3_REGION = env("MOODIST_S3_REGION", "us-east-1")
S3_PRESIGN_TTL = int(env("MOODIST_S3_PRESIGN_TTL", "604800"))
LOCAL_STORAGE_DIR = env("MOODIST_LOCAL_STORAGE_DIR", "")

# محدودیت آپلود تصویر.
MAX_IMAGE_BYTES = int(env("MOODIST_MAX_IMAGE_BYTES", str(8 * 1024 * 1024)))
MAX_IMAGE_PIXELS = int(env("MOODIST_MAX_IMAGE_PIXELS", "12000000"))
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


def validate_production_config() -> None:
    """خطاهای پیکربندی production را جمع می‌کند و در صورت وجود، راه‌اندازی را متوقف می‌کند."""
    problems: list[str] = []
    if SECRET_KEY == "dev-insecure-secret-change-me":
        problems.append("MOODIST_SECRET_KEY باید در production مقدار امن داشته باشد")
    if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
        problems.append("DATABASE_URL باید در production به PostgreSQL اشاره کند")
    if VISION_PROVIDER != "llm":
        problems.append("MOODIST_VISION_PROVIDER باید llm باشد (تحلیل heuristic فقط توسعه/تست)")
    elif not (LLM_API_URL and LLM_API_KEY and LLM_MODEL):
        problems.append("تنظیمات LLM (MOODIST_LLM_API_URL/KEY/MODEL) ناقص است")
    if STORAGE_BACKEND != "s3":
        problems.append("MOODIST_STORAGE_BACKEND باید s3 باشد (دیسک محلی فقط توسعه)")
    elif not S3_BUCKET:
        problems.append("MOODIST_S3_BUCKET باید تنظیم شود")
    if problems:
        raise RuntimeError(
            "پیکربندی production نامعتبر است:\n- " + "\n- ".join(problems)
        )
