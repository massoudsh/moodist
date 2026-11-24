"""Moodist — FastAPI MVP دستیار تصمیم خرید لباس.

اجرا: uvicorn app.main:app --reload --app-dir moodist
"""

import os
import uuid
from datetime import date
from io import BytesIO

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app import config
from app.database import Base, engine, get_db
from app.matcher import decide
from app.models import (
    PurchaseHistory,
    ProductQuery,
    Recommendation,
    SavedOutfit,
    TasteProfile,
    User,
    WardrobeItem,
)
from app.schemas import (
    ITEM_SEASON,
    OCCASION,
    SEASON,
    OutfitOut,
    PackingPlanOut,
    PurchaseDecisionIn,
    RecommendationOut,
    SavedOutfitIn,
    SavedOutfitOut,
    StyleQuestionIn,
    TasteProfileIn,
    TasteProfileOut,
    UserCreate,
    UserOut,
    WardrobeAnalysisOut,
    WardrobeItemOut,
    WardrobeItemUpdateIn,
    WardrobeItemWearIn,
    WearStatsOut,
)
from app.styling import (
    analyze_wardrobe,
    packing_plan,
    shopping_guidance,
    style_advice,
    suggest_outfits,
)
from app.vision import HeuristicVisionAnalyzer
from app.wear import wardrobe_stats
from app.weather import weather_for
from backend.competitors import get_competitor_report, get_iran_competitor_report
from backend.pages import get_page, page_list

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = config.LOCAL_STORAGE_DIR or os.path.join(BASE_DIR, "storage", "images")
os.makedirs(STORAGE_DIR, exist_ok=True)

if config.IS_PRODUCTION:
    config.validate_production_config()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Moodist API (MVP)")
vision_analyzer = HeuristicVisionAnalyzer()


def _read_image(upload: UploadFile) -> tuple[bytes, str]:
    if upload.content_type not in config.ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(415, "فرمت تصویر پشتیبانی نمی‌شود")

    data = upload.file.read(config.MAX_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(400, "تصویر خالی است")
    if len(data) > config.MAX_IMAGE_BYTES:
        raise HTTPException(413, "حجم تصویر بیش از حد مجاز است")

    try:
        with Image.open(BytesIO(data)) as image:
            image.verify()
        with Image.open(BytesIO(data)) as image:
            image_format = image.format
            width, height = image.size
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "فایل تصویر معتبر نیست")

    if image_format not in config.ALLOWED_IMAGE_FORMATS:
        raise HTTPException(415, "فرمت تصویر پشتیبانی نمی‌شود")
    if width * height > config.MAX_IMAGE_PIXELS:
        raise HTTPException(413, "ابعاد تصویر بیش از حد مجاز است")
    return data, image_format.lower()


def _save_image(data: bytes, image_format: str) -> str:
    filename = f"{uuid.uuid4().hex}.{image_format}"
    path = os.path.join(STORAGE_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path


@app.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "این ایمیل قبلاً ثبت شده است")
    user = User(name=payload.name, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/taste-profile", response_model=TasteProfileOut)
def upsert_taste_profile(payload: TasteProfileIn, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(404, "کاربر پیدا نشد")

    profile = db.query(TasteProfile).filter(TasteProfile.user_id == payload.user_id).first()
    if profile is None:
        profile = TasteProfile(user_id=payload.user_id)
        db.add(profile)

    profile.preferred_colors = payload.preferred_colors
    profile.preferred_styles = payload.preferred_styles
    profile.budget_min = payload.budget_min
    profile.budget_max = payload.budget_max
    profile.size = payload.size
    db.commit()
    db.refresh(profile)
    return profile


@app.post("/wardrobe", response_model=WardrobeItemOut)
def add_wardrobe_item(
    user_id: int = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
    season: ITEM_SEASON = Form("all"),
    purchase_price: float | None = Form(None),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "کاربر پیدا نشد")
    if purchase_price is not None and purchase_price < 0:
        raise HTTPException(422, "قیمت نمی‌تواند منفی باشد")

    data, image_format = _read_image(image)
    result = vision_analyzer.analyze(data, category_hint=category)
    image_path = _save_image(data, image_format)

    item = WardrobeItem(
        user_id=user_id,
        image_path=image_path,
        category=result.category,
        dominant_color=result.dominant_color,
        style=result.style,
        season=season,
        purchase_price=purchase_price,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/analyze", response_model=RecommendationOut)
def analyze_product(
    user_id: int = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),
    price: float | None = Form(None),
    db: Session = Depends(get_db),
):
    """عکس لباس/محصول می‌گیرد، با کمد و سلیقهٔ کاربر مقایسه می‌کند و بخر/نخر برمی‌گرداند."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "کاربر پیدا نشد")

    data, image_format = _read_image(image)
    vision_result = vision_analyzer.analyze(data, category_hint=category)
    image_path = _save_image(data, image_format)

    query = ProductQuery(
        user_id=user_id,
        source_type="image",
        source_value=image_path,
        extracted_category=vision_result.category,
        extracted_color=vision_result.dominant_color,
        extracted_style=vision_result.style,
    )
    db.add(query)
    db.commit()
    db.refresh(query)

    wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
    taste = db.query(TasteProfile).filter(TasteProfile.user_id == user_id).first()

    decision = decide(vision_result, wardrobe, taste, price=price)

    recommendation = Recommendation(
        product_query_id=query.id,
        verdict=decision.verdict,
        score=decision.score,
        reasons=decision.reasons,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    return RecommendationOut(
        product_query_id=query.id,
        verdict=recommendation.verdict,
        score=recommendation.score,
        reasons=recommendation.reasons,
        extracted_category=vision_result.category,
        extracted_color=vision_result.dominant_color,
    )


@app.post("/purchase-history")
def record_purchase_decision(payload: PurchaseDecisionIn, db: Session = Depends(get_db)):
    query = db.get(ProductQuery, payload.product_query_id)
    if not query or query.user_id != payload.user_id:
        raise HTTPException(404, "درخواست تحلیل موردنظر پیدا نشد")

    history = PurchaseHistory(
        user_id=payload.user_id,
        product_query_id=payload.product_query_id,
        decision=payload.decision,
    )
    db.add(history)
    db.commit()
    return {"status": "ok"}


@app.get("/purchase-history/{user_id}")
def list_purchase_history(user_id: int, db: Session = Depends(get_db)):
    return (
        db.query(PurchaseHistory)
        .filter(PurchaseHistory.user_id == user_id)
        .order_by(PurchaseHistory.decided_at.desc())
        .all()
    )


def _user_wardrobe(
    db: Session, user_id: int, include_archived: bool = False
) -> list[WardrobeItem]:
    if not db.get(User, user_id):
        raise HTTPException(404, "کاربر پیدا نشد")
    query = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id)
    if not include_archived:
        query = query.filter(WardrobeItem.archived.is_(False))
    return query.all()


@app.get("/wardrobe/analysis/{user_id}", response_model=WardrobeAnalysisOut)
def wardrobe_analysis(user_id: int, db: Session = Depends(get_db)):
    return analyze_wardrobe(_user_wardrobe(db, user_id))


@app.get("/outfits/{user_id}", response_model=list[OutfitOut])
def outfits(
    user_id: int,
    occasion: OCCASION = "casual",
    season: SEASON | None = None,
    db: Session = Depends(get_db),
):
    return suggest_outfits(
        _user_wardrobe(db, user_id), occasion=occasion, season=season
    )


@app.get("/outfits/today/{user_id}")
def outfit_of_the_day(
    user_id: int,
    occasion: OCCASION = "casual",
    temperature_c: float | None = None,
    condition: str = "clear",
    db: Session = Depends(get_db),
):
    """پیشنهاد روز: ست متناسب با هوا و فصل."""
    wardrobe = _user_wardrobe(db, user_id)
    weather = weather_for(temperature_c=temperature_c, condition=condition)
    suggestions = suggest_outfits(
        wardrobe, occasion=occasion, limit=3, season=weather.season
    )
    return {
        "date": date.today().isoformat(),
        "weather": {
            "season": weather.season,
            "temperature_c": weather.temperature_c,
            "condition": weather.condition,
            "advice": weather.advice,
        },
        "outfits": suggestions,
    }


@app.get("/packing-plan/{user_id}", response_model=PackingPlanOut)
def get_packing_plan(
    user_id: int,
    days: int = 3,
    season: SEASON | None = None,
    db: Session = Depends(get_db),
):
    wardrobe = _user_wardrobe(db, user_id)
    plan = packing_plan(wardrobe, days=days, season=season)
    return PackingPlanOut(
        days=plan.days,
        season=plan.season,
        items=plan.items,
        missing_categories=plan.missing_categories,
        notes=plan.notes,
    )


@app.post("/style-advice")
def ask_style(payload: StyleQuestionIn, db: Session = Depends(get_db)):
    wardrobe = _user_wardrobe(db, payload.user_id)
    return {"answer": style_advice(wardrobe, payload.question)}


@app.get("/shopping-guidance/{user_id}")
def get_shopping_guidance(user_id: int, db: Session = Depends(get_db)):
    return {"suggestions": shopping_guidance(_user_wardrobe(db, user_id))}


@app.patch("/wardrobe/{item_id}", response_model=WardrobeItemOut)
def update_wardrobe_item(
    item_id: int, payload: WardrobeItemUpdateIn, db: Session = Depends(get_db)
):
    item = db.get(WardrobeItem, item_id)
    if not item:
        raise HTTPException(404, "آیتم کمد پیدا نشد")
    if payload.purchase_price is not None and payload.purchase_price < 0:
        raise HTTPException(422, "قیمت نمی‌تواند منفی باشد")

    for field in ("category", "style", "season", "purchase_price"):
        value = getattr(payload, field)
        if value is not None:
            setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@app.delete("/wardrobe/{item_id}")
def archive_wardrobe_item(item_id: int, db: Session = Depends(get_db)):
    """آیتم را بایگانی می‌کند (حذف نرم) تا تاریخچه و آمار از دست نرود."""
    item = db.get(WardrobeItem, item_id)
    if not item:
        raise HTTPException(404, "آیتم کمد پیدا نشد")
    item.archived = True
    db.commit()
    return {"status": "archived"}


@app.post("/wardrobe/{item_id}/wear", response_model=WardrobeItemOut)
def record_wear(
    item_id: int, payload: WardrobeItemWearIn, db: Session = Depends(get_db)
):
    item = db.get(WardrobeItem, item_id)
    if not item:
        raise HTTPException(404, "آیتم کمد پیدا نشد")
    item.times_worn = (item.times_worn or 0) + payload.times
    db.commit()
    db.refresh(item)
    return item


@app.get("/wardrobe/stats/{user_id}", response_model=WearStatsOut)
def get_wear_stats(user_id: int, db: Session = Depends(get_db)):
    return wardrobe_stats(_user_wardrobe(db, user_id, include_archived=True))


@app.post("/outfits/saved", response_model=SavedOutfitOut)
def save_outfit(payload: SavedOutfitIn, db: Session = Depends(get_db)):
    if not db.get(User, payload.user_id):
        raise HTTPException(404, "کاربر پیدا نشد")

    owned = {
        item.id
        for item in db.query(WardrobeItem)
        .filter(
            WardrobeItem.user_id == payload.user_id,
            WardrobeItem.id.in_(payload.item_ids),
        )
        .all()
    }
    unknown = sorted(set(payload.item_ids) - owned)
    if unknown:
        raise HTTPException(404, f"آیتم کمد پیدا نشد: {unknown}")

    outfit = SavedOutfit(
        user_id=payload.user_id,
        name=payload.name,
        occasion=payload.occasion,
        item_ids=payload.item_ids,
        planned_for=payload.planned_for,
    )
    db.add(outfit)
    db.commit()
    db.refresh(outfit)
    return outfit


@app.get("/outfits/saved/{user_id}", response_model=list[SavedOutfitOut])
def list_saved_outfits(user_id: int, db: Session = Depends(get_db)):
    if not db.get(User, user_id):
        raise HTTPException(404, "کاربر پیدا نشد")
    return (
        db.query(SavedOutfit)
        .filter(SavedOutfit.user_id == user_id)
        .order_by(SavedOutfit.created_at.desc())
        .all()
    )


@app.delete("/outfits/saved/{outfit_id}")
def delete_saved_outfit(outfit_id: int, db: Session = Depends(get_db)):
    outfit = db.get(SavedOutfit, outfit_id)
    if not outfit:
        raise HTTPException(404, "ست ذخیره‌شده پیدا نشد")
    db.delete(outfit)
    db.commit()
    return {"status": "deleted"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/pages")
def list_pages():
    return {"pages": page_list()}


@app.get("/pages/{slug}")
def page_definition(slug: str):
    page = get_page(slug)
    if page is None:
        raise HTTPException(404, "صفحه پیدا نشد")
    return page


@app.get("/competitors/iran")
def iran_competitor_report():
    return get_iran_competitor_report()


@app.get("/competitors/market")
def market_competitor_report():
    """پنج رقیب ایرانی و پنج رقیب بین‌المللی به‌همراه قابلیت‌های پیاده‌شده."""
    return get_competitor_report()
