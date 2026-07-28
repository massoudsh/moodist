"""FastAPI MVP — دستیار تصمیم خرید لباس.

اجرا: uvicorn app.main:app --reload --app-dir wardrobe-advisor
"""

import os
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

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
    TasteProfileIn,
    TasteProfileOut,
    UserCreate,
    UserOut,
    WardrobeItemOut,
)
from app.vision import HeuristicVisionAnalyzer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage", "images")
os.makedirs(STORAGE_DIR, exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wardrobe Advisor API (MVP)")
vision_analyzer = HeuristicVisionAnalyzer()


def _save_image(data: bytes) -> str:
    filename = f"{uuid.uuid4().hex}.jpg"
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

    data = image.file.read()
    result = vision_analyzer.analyze(data, category_hint=category)
    image_path = _save_image(data)

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

    data = image.file.read()
    vision_result = vision_analyzer.analyze(data, category_hint=category)
    image_path = _save_image(data)

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
    if payload.decision not in ("bought", "skipped"):
        raise HTTPException(400, "decision باید bought یا skipped باشد")

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
