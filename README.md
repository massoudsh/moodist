# moodist

این ریپو دو پروژه‌ی مستقل را در خود جای داده — هرکدام در یک subdirectory جدا و بدون وابستگی به یکدیگر.

## Moodist — اپ صداهای محیطی

اپلیکیشن صداهای محیطی (ambient sounds) برای تمرکز، آرامش و خواب. کاربر چند صدا (باران، جنگل،
کافه، نویز سفید و ...) را همزمان با ولوم مستقل ترکیب می‌کند تا یک soundscape شخصی بسازد —
کاملاً client-side، بدون نیاز به حساب کاربری.

**وضعیت فعلی:** فقط صفحه‌ی معرفی (`landing/`) و مستندات (`docs/`) ساخته شده؛ اپ اصلی (مکسر صدا)
هنوز پیاده‌سازی نشده است.

**پشته برنامه‌ریزی‌شده:** Vite + React + TypeScript + Web Audio API.

| مسیر | توضیح |
|---|---|
| `landing/` | صفحه معرفی محصول — HTML/CSS/JS خالص، بدون build step |
| `docs/architecture.md` | معماری و پشته فناوری |
| `docs/roadmap.md` | نقشه‌راه توسعه (۵ فاز، از MVP تا self-host) |

### اجرای لندینگ

فایل `landing/index.html` را مستقیم در مرورگر باز کن، یا با یک static server ساده سرو کن:

```bash
cd landing
python3 -m http.server 8080
```

## Wardrobe Advisor — دستیار تصمیم خرید لباس

استایلیست هوشمند خرید: عکس یک لباس/محصول را می‌گیرد، با کمد و سلیقه‌ی ذخیره‌شده‌ی کاربر مقایسه
می‌کند و پاسخ «بخر/نخر + دلیل» برمی‌گرداند.

**وضعیت فعلی:** MVP کامل پیاده‌سازی و تست شده — FastAPI + SQLAlchemy + SQLite، تحلیل تصویر با
یک `VisionAnalyzer` قابل‌تعویض (heuristic رنگ غالب در MVP → مدل چندوجهی واقعی در production).

| مسیر | توضیح |
|---|---|
| `wardrobe-advisor/app/` | endpointها، مدل‌های داده، منطق تحلیل و تصمیم‌گیری |
| `wardrobe-advisor/tests/` | تست‌های end-to-end |
| `wardrobe-advisor/docs/prd.md` | سند محصول |
| `wardrobe-advisor/docs/architecture.md` | معماری و مدل داده کامل |

### اجرا

```bash
cd wardrobe-advisor
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

### تست

```bash
cd wardrobe-advisor
pytest
```

### Endpointهای اصلی

| Endpoint | توضیح |
|---|---|
| `POST /users` | ساخت کاربر |
| `POST /taste-profile` | ثبت/به‌روزرسانی سلیقه (رنگ/سبک/بودجه/سایز) |
| `POST /wardrobe` | افزودن آیتم به کمد (فرم + آپلود عکس) |
| `POST /analyze` | عکس/دسته می‌گیرد → verdict، score و دلایل بخر/نخر |
| `POST /purchase-history` | ثبت تصمیم نهایی کاربر (bought/skipped) |
| `GET /purchase-history/{user_id}` | تاریخچه‌ی تصمیم‌های کاربر |
