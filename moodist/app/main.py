"""Moodist — FastAPI MVP دستیار تصمیم خرید لباس.

اجرا: uvicorn app.main:app --reload --app-dir moodist
"""

import os
import uuid
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
    TasteProfile,
    User,
    WardrobeItem,
)
from app.schemas import (
    PurchaseDecisionIn,
    RecommendationOut,
    StyleQuestionIn,
    TasteProfileIn,
    TasteProfileOut,
    UserCreate,
    UserOut,
    WardrobeAnalysisOut,
    WardrobeItemOut,
    OutfitOut,
)
from app.styling import analyze_wardrobe, shopping_guidance, style_advice, suggest_outfits
from app.vision import HeuristicVisionAnalyzer

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
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "کاربر پیدا نشد")

    data, image_format = _read_image(image)
    result = vision_analyzer.analyze(data, category_hint=category)
    image_path = _save_image(data, image_format)

    item = WardrobeItem(
        user_id=user_id,
        image_path=image_path,
        category=result.category,
        dominant_color=result.dominant_color,
        style=result.style,
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


def _user_wardrobe(db: Session, user_id: int) -> list[WardrobeItem]:
    if not db.get(User, user_id):
        raise HTTPException(404, "کاربر پیدا نشد")
    return db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()


@app.get("/wardrobe/analysis/{user_id}", response_model=WardrobeAnalysisOut)
def wardrobe_analysis(user_id: int, db: Session = Depends(get_db)):
    return analyze_wardrobe(_user_wardrobe(db, user_id))


@app.get("/outfits/{user_id}", response_model=list[OutfitOut])
def outfits(user_id: int, occasion: OCCASION = "casual", db: Session = Depends(get_db)):
    return suggest_outfits(_user_wardrobe(db, user_id), occasion=occasion)


@app.post("/style-advice")
def ask_style(payload: StyleQuestionIn, db: Session = Depends(get_db)):
    wardrobe = _user_wardrobe(db, payload.user_id)
    return {"answer": style_advice(wardrobe, payload.question)}


@app.get("/shopping-guidance/{user_id}")
def get_shopping_guidance(user_id: int, db: Session = Depends(get_db)):
    return {"suggestions": shopping_guidance(_user_wardrobe(db, user_id))}
