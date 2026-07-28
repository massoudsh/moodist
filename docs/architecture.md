# معماری Moodist

> اپلیکیشن صداهای محیطی برای تمرکز و آرامش — کاملاً client-side، بدون نیاز به حساب کاربری.

## پشته فناوری (پیشنهادی)
- **Frontend:** Vite + React + TypeScript
- **Audio Engine:** Web Audio API — لایه‌بندی چند صدا با فید کردن نرم (fade in/out) و کنترل ولوم مستقل هر صدا
- **State/Persistence:** localStorage برای presetها؛ query-string/hash برای اشتراک‌گذاری mix از طریق URL
- **PWA:** manifest.json + service worker برای کش آفلاین (فاز ۴)
- **Backend:** ندارد در MVP — همه‌چیز سمت کلاینت. در آینده صرفاً یک static host یا Docker image برای serve کردن build
- **Deployment:** استاتیک (Vercel/Netlify/Docker + nginx)

## لایه‌ها
```
landing/          صفحه معرفی محصول (استاتیک، بدون build — HTML/CSS/JS خالص)
docs/             اسناد معماری و نقشه‌راه
(آینده) app/       اپلیکیشن اصلی React (پلیر و میکسر صدا)
(آینده) public/sounds/   فایل‌های صوتی دسته‌بندی‌شده (Nature, Rain, Urban, Binaural, ...)
```

## جریان اصلی (Mixer)
1. کاربر چند صدا را از دسته‌بندی‌ها انتخاب و پخش می‌کند.
2. هر صدا یک `<audio>`/`AudioBufferSourceNode` مستقل با ولوم و loop خودش دارد.
3. تغییر ولوم یا play/pause با fade نرم (چند صدم ثانیه) انجام می‌شود تا کلیک ناگهانی نشنود.
4. وضعیت میکس (کدام صداها + ولوم هرکدام) در URL و/یا localStorage سریالایز می‌شود.

## قراردادها
- هیچ صدایی نباید بدون رضایت کاربر autoplay شود (سیاست مرورگرها + UX).
- افزودن صدای جدید = یک فایل صوتی + یک ورودی متادیتا (id، نام، دسته، آیکون) — نیازی به تغییر کد مرکزی مکسر نیست.
- ابزارهای جانبی (Pomodoro، sleep timer، breathing) مستقل از مکسر صدا پیاده می‌شوند و فقط در صورت نیاز به آن رویداد می‌فرستند (مثلاً پایان Pomodoro → فید-اوت صداها).

## منابع
- `landing/index.html` — صفحه لندینگ فعلی
- `docs/roadmap.md` — فازبندی توسعه
