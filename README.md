# Moodist

استایلیست هوشمند خرید پوشاک: عکس یک لباس/محصول را می‌گیرد، با کمد و سلیقه‌ی ذخیره‌شده‌ی کاربر
مقایسه می‌کند و پاسخ «بخر/نخر + دلیل» برمی‌گرداند.

**وضعیت فعلی:** MVP کامل پیاده‌سازی و تست شده — FastAPI + SQLAlchemy + SQLite، تحلیل تصویر با
یک `VisionAnalyzer` قابل‌تعویض (heuristic رنگ غالب در MVP → مدل چندوجهی واقعی در production).

| مسیر | توضیح |
|---|---|
| `moodist/app/` | endpointها، مدل‌های داده، منطق تحلیل و تصمیم‌گیری |
| `moodist/tests/` | تست‌های end-to-end |
| `moodist/docs/prd.md` | سند محصول |
| `moodist/docs/architecture.md` | معماری و مدل داده کامل |

جزئیات بیشتر در [ویکی ریپو](https://github.com/massoudsh/moodist/wiki).

## اجرا

```bash
cd moodist
pip install -r requirements.txt
uvicorn app.main:app --reload --app-dir .
```

## تست

```bash
cd moodist
pytest
```

## Endpointهای اصلی

| Endpoint | توضیح |
|---|---|
| `POST /users` | ساخت کاربر |
| `POST /taste-profile` | ثبت/به‌روزرسانی سلیقه (رنگ/سبک/بودجه/سایز) |
| `POST /wardrobe` | افزودن آیتم به کمد (فرم + آپلود عکس) |
| `POST /analyze` | عکس/دسته می‌گیرد → verdict، score و دلایل بخر/نخر |
| `POST /purchase-history` | ثبت تصمیم نهایی کاربر (bought/skipped) |
| `GET /purchase-history/{user_id}` | تاریخچه‌ی تصمیم‌های کاربر |
