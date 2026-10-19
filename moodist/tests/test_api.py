"""تست end-to-end روی endpointهای MVP (بدون وابستگی به سرویس خارجی)."""

import io
import os
import sys

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _solid_color_image(color: tuple[int, int, int]) -> bytes:
    img = Image.new("RGB", (16, 16), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


BLUE = (41, 91, 200)
RED = (200, 30, 30)


def setup_function():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)


def _create_user(email="sara@example.com") -> int:
    resp = client.post("/users", json={"name": "Sara", "email": email})
    assert resp.status_code == 200
    return resp.json()["id"]


def test_create_user():
    user_id = _create_user()
    assert user_id > 0


def test_duplicate_email_rejected():
    _create_user("dup@example.com")
    resp = client.post("/users", json={"name": "X", "email": "dup@example.com"})
    assert resp.status_code == 400


def test_taste_profile_upsert():
    user_id = _create_user()
    resp = client.post(
        "/taste-profile",
        json={
            "user_id": user_id,
            "preferred_colors": ["blue", "black"],
            "preferred_styles": ["casual"],
            "budget_min": 10,
            "budget_max": 100,
            "size": "M",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["preferred_colors"] == ["blue", "black"]


def test_add_wardrobe_item():
    user_id = _create_user()
    resp = client.post(
        "/wardrobe",
        data={"user_id": user_id, "category": "shirt"},
        files={"image": ("shirt.jpg", _solid_color_image(BLUE), "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"] == "shirt"
    assert body["dominant_color"] == "blue"


def test_upload_rejects_non_image_content_type():
    user_id = _create_user()
    resp = client.post(
        "/wardrobe",
        data={"user_id": user_id, "category": "shirt"},
        files={"image": ("shirt.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 415


def test_upload_rejects_invalid_image_content():
    user_id = _create_user()
    resp = client.post(
        "/wardrobe",
        data={"user_id": user_id, "category": "shirt"},
        files={"image": ("shirt.jpg", b"not an image", "image/jpeg")},
    )
    assert resp.status_code == 400


def test_analyze_recommends_dont_buy_for_duplicate_and_mismatched_color():
    user_id = _create_user()
    # سلیقهٔ کاربر: رنگ‌های موردعلاقه فقط قرمز است (آبی جزو سلیقه نیست)
    client.post(
        "/taste-profile",
        json={"user_id": user_id, "preferred_colors": ["red"], "preferred_styles": []},
    )
    # دو آیتم آبی مشابه از قبل در کمد
    for _ in range(2):
        client.post(
            "/wardrobe",
            data={"user_id": user_id, "category": "shirt"},
            files={"image": ("shirt.jpg", _solid_color_image(BLUE), "image/jpeg")},
        )

    resp = client.post(
        "/analyze",
        data={"user_id": user_id, "category": "shirt"},
        files={"image": ("new.jpg", _solid_color_image(BLUE), "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["extracted_color"] == "blue"
    assert body["verdict"] == "dont_buy"
    assert body["score"] < 0.5
    assert any("مشابه" in r for r in body["reasons"])


def test_analyze_recommends_buy_for_new_preferred_color():
    user_id = _create_user()
    client.post(
        "/taste-profile",
        json={"user_id": user_id, "preferred_colors": ["red"], "preferred_styles": []},
    )
    resp = client.post(
        "/analyze",
        data={"user_id": user_id, "category": "jacket"},
        files={"image": ("new.jpg", _solid_color_image(RED), "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["extracted_color"] == "red"
    assert body["verdict"] == "buy"
    assert body["score"] >= 0.5


def test_purchase_history_roundtrip():
    user_id = _create_user()
    analyze_resp = client.post(
        "/analyze",
        data={"user_id": user_id, "category": "jacket"},
        files={"image": ("new.jpg", _solid_color_image(RED), "image/jpeg")},
    )
    product_query_id = analyze_resp.json()["product_query_id"]

    resp = client.post(
        "/purchase-history",
        json={"user_id": user_id, "product_query_id": product_query_id, "decision": "bought"},
    )
    assert resp.status_code == 200

    history = client.get(f"/purchase-history/{user_id}").json()
    assert len(history) == 1
    assert history[0]["decision"] == "bought"


def test_analyze_unknown_user_returns_404():
    resp = client.post(
        "/analyze",
        data={"user_id": 999999, "category": "shirt"},
        files={"image": ("x.jpg", _solid_color_image(BLUE), "image/jpeg")},
    )
    assert resp.status_code == 404


def _add_item(user_id: int, category: str, color: tuple[int, int, int]) -> None:
    resp = client.post(
        "/wardrobe",
        data={"user_id": user_id, "category": category},
        files={"image": (f"{category}.jpg", _solid_color_image(color), "image/jpeg")},
    )
    assert resp.status_code == 200


def test_purchase_history_rejects_invalid_decision():
    user_id = _create_user()
    analyze_resp = client.post(
        "/analyze",
        data={"user_id": user_id, "category": "jacket"},
        files={"image": ("new.jpg", _solid_color_image(RED), "image/jpeg")},
    )
    product_query_id = analyze_resp.json()["product_query_id"]

    resp = client.post(
        "/purchase-history",
        json={"user_id": user_id, "product_query_id": product_query_id, "decision": "maybe"},
    )
    assert resp.status_code == 422


def test_wardrobe_analysis_reports_missing_and_dominant():
    user_id = _create_user()
    _add_item(user_id, "shirt", BLUE)
    _add_item(user_id, "t-shirt", BLUE)

    resp = client.get(f"/wardrobe/analysis/{user_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_items"] == 2
    assert body["dominant_colors"] == ["blue"]
    assert "bottom" in body["missing_categories"]
    assert "shoes" in body["missing_categories"]


def test_wardrobe_analysis_unknown_user_returns_404():
    resp = client.get("/wardrobe/analysis/999999")
    assert resp.status_code == 404


def test_outfits_built_from_wardrobe():
    user_id = _create_user()
    _add_item(user_id, "shirt", BLUE)
    _add_item(user_id, "pants", (30, 30, 30))

    resp = client.get(f"/outfits/{user_id}", params={"occasion": "casual"})
    assert resp.status_code == 200
    outfits = resp.json()
    assert len(outfits) == 1
    categories = {item["category"] for item in outfits[0]["items"]}
    assert categories == {"shirt", "pants"}
    assert outfits[0]["matched_color"] == "blue"


def test_outfits_invalid_occasion_returns_422():
    user_id = _create_user()
    resp = client.get(f"/outfits/{user_id}", params={"occasion": "space"})
    assert resp.status_code == 422


def test_outfits_empty_wardrobe_returns_empty_list():
    user_id = _create_user()
    resp = client.get(f"/outfits/{user_id}")
    assert resp.status_code == 200
    assert resp.json() == []


def test_style_advice_answers_color_question():
    user_id = _create_user()
    _add_item(user_id, "shirt", RED)

    resp = client.post(
        "/style-advice",
        json={"user_id": user_id, "question": "رنگ غالب کمد من چیست؟"},
    )
    assert resp.status_code == 200
    assert "red" in resp.json()["answer"]


def test_shopping_guidance_suggests_missing_categories():
    user_id = _create_user()
    _add_item(user_id, "shirt", BLUE)

    resp = client.get(f"/shopping-guidance/{user_id}")
    assert resp.status_code == 200
    suggestions = resp.json()["suggestions"]
    assert any("bottom" in s for s in suggestions)
