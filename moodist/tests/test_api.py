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


def test_pages_contract_lists_product_pages():
    resp = client.get("/pages")
    assert resp.status_code == 200
    slugs = {page["path"] for page in resp.json()["pages"]}
    assert {"/", "/wardrobe", "/outfits", "/discover", "/profile"} <= slugs


def test_page_definition_and_unknown_page():
    resp = client.get("/pages/wardrobe")
    assert resp.status_code == 200
    assert resp.json()["title"] == "کمد من"

    missing = client.get("/pages/unknown")
    assert missing.status_code == 404


def test_iran_competitor_report_has_five_rivals():
    resp = client.get("/competitors/iran")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["competitors"]) == 5
    assert all(item["source"].startswith("https://") for item in body["competitors"])


def _add_item_full(
    user_id: int,
    category: str,
    color: tuple[int, int, int],
    season: str = "all",
    price: float | None = None,
) -> dict:
    data = {"user_id": user_id, "category": category, "season": season}
    if price is not None:
        data["purchase_price"] = price
    resp = client.post(
        "/wardrobe",
        data=data,
        files={"image": (f"{category}.jpg", _solid_color_image(color), "image/jpeg")},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_wardrobe_item_starts_with_wear_and_season_defaults():
    user_id = _create_user()
    item = _add_item_full(user_id, "shirt", BLUE, season="summer", price=120.0)
    assert item["season"] == "summer"
    assert item["purchase_price"] == 120.0
    assert item["times_worn"] == 0
    assert item["archived"] is False


def test_negative_purchase_price_rejected():
    user_id = _create_user()
    resp = client.post(
        "/wardrobe",
        data={"user_id": user_id, "category": "shirt", "purchase_price": -5},
        files={"image": ("s.jpg", _solid_color_image(BLUE), "image/jpeg")},
    )
    assert resp.status_code == 422


def test_patch_wardrobe_item_updates_metadata():
    user_id = _create_user()
    item = _add_item_full(user_id, "shirt", BLUE)
    resp = client.patch(
        f"/wardrobe/{item['id']}",
        json={"season": "winter", "purchase_price": 80, "style": "minimal"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["season"] == "winter"
    assert body["purchase_price"] == 80.0
    assert body["style"] == "minimal"


def test_patch_unknown_item_returns_404():
    resp = client.patch("/wardrobe/999999", json={"season": "winter"})
    assert resp.status_code == 404


def test_wear_tracking_and_cost_per_wear():
    user_id = _create_user()
    item = _add_item_full(user_id, "shoes", BLUE, price=200.0)

    resp = client.post(f"/wardrobe/{item['id']}/wear", json={"times": 4})
    assert resp.status_code == 200
    assert resp.json()["times_worn"] == 4

    stats = client.get(f"/wardrobe/stats/{user_id}")
    assert stats.status_code == 200
    body = stats.json()
    assert body["total_items"] == 1
    assert body["tracked_items"] == 1
    assert body["total_spend"] == 200.0
    assert body["total_wears"] == 4
    assert body["average_cost_per_wear"] == 50.0
    assert body["best_value"][0]["cost_per_wear"] == 50.0


def test_archiving_item_hides_it_from_outfits_but_keeps_stats():
    user_id = _create_user()
    shirt = _add_item_full(user_id, "shirt", BLUE)
    _add_item_full(user_id, "pants", (30, 30, 30), price=90.0)

    before = client.get(f"/outfits/{user_id}").json()
    assert len(before) == 1
    resp = client.delete(f"/wardrobe/{shirt['id']}")
    assert resp.status_code == 200
    after = client.get(f"/outfits/{user_id}").json()
    assert all(item["id"] != shirt["id"] for outfit in after for item in outfit["items"])

    stats = client.get(f"/wardrobe/stats/{user_id}").json()
    assert stats["total_items"] == 2


def test_outfits_filter_by_season():
    user_id = _create_user()
    _add_item_full(user_id, "shirt", BLUE, season="summer")
    _add_item_full(user_id, "pants", (30, 30, 30), season="winter")

    summer = client.get(f"/outfits/{user_id}", params={"season": "summer"}).json()
    assert all(item["category"] == "shirt" for outfit in summer for item in outfit["items"])

    resp = client.get(f"/outfits/{user_id}", params={"season": "monsoon"})
    assert resp.status_code == 422


def test_outfit_of_the_day_uses_weather():
    user_id = _create_user()
    _add_item_full(user_id, "shirt", BLUE, season="summer")

    resp = client.get(
        f"/outfits/today/{user_id}", params={"temperature_c": 33, "condition": "clear"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["weather"]["season"] == "summer"
    assert len(body["outfits"]) == 1

    rainy = client.get(
        f"/outfits/today/{user_id}", params={"temperature_c": 12, "condition": "rain"}
    ).json()
    assert "بارانی" in rainy["weather"]["advice"]


def test_packing_plan_returns_items_and_notes():
    user_id = _create_user()
    _add_item_full(user_id, "shirt", BLUE, season="summer")
    _add_item_full(user_id, "pants", (30, 30, 30), season="summer")

    resp = client.get(f"/packing-plan/{user_id}", params={"days": 5, "season": "summer"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["days"] == 5
    assert {item["category"] for item in body["items"]} == {"shirt", "pants"}
    assert body["missing_categories"]
    assert body["notes"]


def test_saved_outfit_roundtrip():
    user_id = _create_user()
    shirt = _add_item_full(user_id, "shirt", BLUE)
    pants = _add_item_full(user_id, "pants", (30, 30, 30))

    resp = client.post(
        "/outfits/saved",
        json={
            "user_id": user_id,
            "name": "مصاحبه",
            "occasion": "formal",
            "item_ids": [shirt["id"], pants["id"]],
        },
    )
    assert resp.status_code == 200
    outfit_id = resp.json()["id"]

    listed = client.get(f"/outfits/saved/{user_id}").json()
    assert len(listed) == 1
    assert listed[0]["name"] == "مصاحبه"

    assert client.delete(f"/outfits/saved/{outfit_id}").status_code == 200
    assert client.get(f"/outfits/saved/{user_id}").json() == []


def test_saved_outfit_rejects_items_owned_by_another_user():
    owner = _create_user("owner@example.com")
    other = _create_user("other@example.com")
    item = _add_item_full(owner, "shirt", BLUE)

    resp = client.post(
        "/outfits/saved",
        json={"user_id": other, "name": "x", "item_ids": [item["id"]]},
    )
    assert resp.status_code == 404


def test_market_report_covers_iran_and_international_rivals():
    resp = client.get("/competitors/market")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["competitors"]) == 5
    assert len(body["international"]) == 5
    assert len(body["implemented_features"]) == 5
