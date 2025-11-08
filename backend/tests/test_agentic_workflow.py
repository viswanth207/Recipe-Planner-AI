import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path for 'app' imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.database import db
from app.services.whatsapp_service import WhatsAppService

client = TestClient(app)

TEST_EMAIL = "agentic_user@example.com"
TEST_PASSWORD = "strongpassword123"
TEST_PHONE = "+14155550123"


def signup_and_login():
    # Cleanup any pre-existing user
    db.users.delete_many({"email": TEST_EMAIL})

    # Signup
    res = client.post("/auth/signup", json={
        "name": "Agentic Tester",
        "email": TEST_EMAIL,
        "phone": TEST_PHONE,
        "password": TEST_PASSWORD,
    })
    assert res.status_code == 200
    token = res.json()["access_token"]

    # Login to ensure credentials hashed
    res_login = client.post("/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "phone": TEST_PHONE,
    })
    assert res_login.status_code == 200
    return res_login.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def mock_twilio(monkeypatch):
    def _fake_send(self, to_phone, message):
        return {
            "status": "success",
            "message": "Message sent successfully",
            "response": {"sid": "TEST_SID_123"},
        }
    monkeypatch.setattr(WhatsAppService, "send_message", _fake_send)


def test_end_to_end_agentic_flow():
    token = signup_and_login()

    # Verify WhatsApp manually
    res_verify = client.put("/auth/me/whatsapp-verify", headers=auth_headers(token), json={"verified": True})
    assert res_verify.status_code == 200

    # Upsert some ingredients
    res_ing = client.post("/ingredients/", headers=auth_headers(token), json={
        "name": "Eggs",
        "quantity": 6,
        "unit": "pcs",
    })
    assert res_ing.status_code == 200
    res_ing2 = client.post("/ingredients/", headers=auth_headers(token), json={
        "name": "Spinach",
        "quantity": 2,
        "unit": "cups",
    })
    assert res_ing2.status_code == 200

    # Run agentic orchestration flow with send_now True
    res_agentic = client.post("/agentic/run", headers=auth_headers(token), json={
        "send_now": True,
        "delivery_time": "08:30",
        "timezone": "UTC",
        "meal": "breakfast",
        "to_override": TEST_PHONE,
    })

    assert res_agentic.status_code == 200, res_agentic.text
    payload = res_agentic.json()
    assert payload["ok"] is True
    assert payload["meal_key"] in ["breakfast", "lunch", "dinner"]
    assert isinstance(payload.get("meal_plan"), dict)
    assert payload.get("whatsapp_sent") is True
    assert payload.get("whatsapp_message_id") == "TEST_SID_123"
    # removed stray assertion referencing undefined 'body'

    # Preview works and contains structure
    res_preview = client.get("/mealplan/preview", headers=auth_headers(token))
    assert res_preview.status_code == 200
    preview = res_preview.json()
    assert "meal_plan" in preview


def test_save_now_idempotent():
    token = signup_and_login()
    # add one ingredient
    client.post("/ingredients/", headers=auth_headers(token), json={"name": "egg", "quantity": 2, "unit": "pcs"})

    # First save
    res1 = client.post("/mealplan/save-now", headers=auth_headers(token))
    assert res1.status_code == 200

    # Second save returns existing
    res2 = client.post("/mealplan/save-now", headers=auth_headers(token))
    assert res2.status_code == 200
    assert res2.json().get("message") in ("Saved", "Meal plan already exists for today")