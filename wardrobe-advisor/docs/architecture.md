# معماری — Wardrobe Advisor

## استک انتخابی
| لایه | انتخاب | دلیل |
|---|---|---|
| Backend framework | **FastAPI** (Python) | async، مناسب فراخوانی مدل AI، اسکیمای خودکار با Pydantic، سریع برای پروتوتایپ |
| DB | **SQLite** در MVP → **PostgreSQL** در production | SQLite صفر-کانفیگ برای پروتوتایپ؛ مدل رابطه‌ای مناسب دادهٔ ساختاریافته (کمد/سلیقه/تاریخچه) |
| ORM | SQLAlchemy 2.x | استاندارد پایتون، مسیر ساده به PostgreSQL در آینده |
| ذخیرهٔ تصویر | MVP: دیسک محلی (`storage/images/`) → Production: S3-compatible (MinIO/S3) | برای پروتوتایپ نیازی به سرویس خارجی نیست؛ مسیر مهاجرت به object storage روشن است |
| مدل چندوجهی (Vision) | Interface قابل‌تعویض (`VisionAnalyzer`) — MVP: پیاده‌سازی heuristic (رنگ غالب با Pillow)، Production: مدل VLM واقعی (مثل یک مدل چندوجهی چت/تصویر) پشت همان interface | جداسازی منطق تجاری از ارائه‌دهندهٔ مدل؛ در سندباکس فعلی تماس شبکه‌ای به مدل خارجی انجام نمی‌شود |

## مدل داده (کامل)

```
User
  id (PK)
  name
  email (unique)
  created_at

TasteProfile
  id (PK)
  user_id (FK -> User.id)
  preferred_colors   (JSON: ["black", "beige", ...])
  preferred_styles   (JSON: ["casual", "minimal", ...])
  budget_min
  budget_max
  size               (string, مثل "M")

WardrobeItem
  id (PK)
  user_id (FK -> User.id)
  image_path
  category      (مثل "shirt", "pants", "jacket")
  dominant_color
  style          (nullable)
  created_at

ProductQuery
  id (PK)
  user_id (FK -> User.id)
  source_type     ("image" | "url")
  source_value    (مسیر فایل آپلودی یا URL)
  extracted_category
  extracted_color
  extracted_style (nullable)
  created_at

Recommendation
  id (PK)
  product_query_id (FK -> ProductQuery.id)
  verdict          ("buy" | "dont_buy")
  score            (float 0..1)
  reasons          (JSON: ["..."])
  created_at

PurchaseHistory
  id (PK)
  user_id (FK -> User.id)
  product_query_id (FK -> ProductQuery.id)
  decision        ("bought" | "skipped")
  decided_at
```

روابط: `User 1—N TasteProfile(1)`, `User 1—N WardrobeItem`, `User 1—N ProductQuery`,
`ProductQuery 1—1 Recommendation`, `User 1—N PurchaseHistory`.

## جریان تحلیل (Analyze Flow)
```
POST /analyze  { user_id, image (upload) یا product_url }
   │
   ├─ 1. اگر url → (فاز بعد) fetch صفحه و استخراج عکس محصول
   │    اگر image → ذخیرهٔ فایل در storage/images/
   │
   ├─ 2. VisionAnalyzer.analyze(image) → { category, dominant_color, style }
   │        (MVP: heuristic رنگ‌غالب با Pillow؛ Production: VLM واقعی)
   │
   ├─ 3. Matcher:
   │      - wardrobe_similarity: چند آیتم مشابه (رنگ+دسته) در کمد وجود دارد؟
   │      - taste_fit: رنگ/سبک در preferred_colors/styles کاربر هست؟
   │      - budget_fit: (اگر قیمت موجود بود) داخل بودجه هست؟
   │      → score نهایی + لیست reasons
   │
   └─ 4. ذخیرهٔ ProductQuery + Recommendation → پاسخ به کاربر
```

## چرا این معماری برای MVP کافی است
- بدون وابستگی به سرویس خارجی قابل اجرا و تست است (heuristic رنگ به‌جای فراخوانی واقعی VLM).
- `VisionAnalyzer` به‌صورت interface طراحی شده — جایگزینی با یک مدل چندوجهی واقعی فقط نیازمند
  پیاده‌سازی یک کلاس جدید است، بدون تغییر در API یا مدل داده.
- مسیر مهاجرت SQLite→PostgreSQL و local-disk→S3 صرفاً تغییر connection/adapter است، نه ری‌رایت.

## ساختار پوشه‌ها
```
wardrobe-advisor/
  docs/
    prd.md            سند محصول
    architecture.md    همین سند
  app/
    main.py            FastAPI app + endpointها
    database.py         اتصال SQLite + session
    models.py            مدل‌های SQLAlchemy
    schemas.py           اسکیمای Pydantic (ورودی/خروجی API)
    vision.py            VisionAnalyzer (interface + پیاده‌سازی heuristic)
    matcher.py           منطق امتیازدهی بخر/نخر
  tests/
    test_api.py          تست‌های end-to-end روی endpointها
```
