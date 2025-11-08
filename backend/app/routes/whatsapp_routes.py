from fastapi import APIRouter, Request, Depends, HTTPException, Query, Response
from app.services.whatsapp_service import process_whatsapp_reply
from pydantic import BaseModel
from typing import Optional
from app.auth import decode_access_token
from app.database import users_col, ingredients_col, mealplans_col

from datetime import datetime
from app.services.whatsapp_service import send_mealplan_whatsapp, send_template_whatsapp
from app.config import WHATSAPP_VERIFY_TOKEN
import re
import pytz

# Import meal plan generator (Gemini preferred, fallback to OpenAI)
try:
    from app.services.gemini_service import generate_meal_plan
except ImportError:
    from app.services.ai_service import generate_meal_plan

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

@router.get("/webhook")
async def whatsapp_webhook_verify(request: Request):
    # Meta Cloud sends hub.* query params
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    verify_token = request.query_params.get("hub.verify_token")
    if mode == "subscribe" and verify_token == WHATSAPP_VERIFY_TOKEN:
        return Response(content=challenge or "OK", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    # Support both Meta Cloud (JSON) and Twilio (form-encoded) inbound webhooks
    processed = False
    try:
        # Try Meta Cloud JSON payload
        data = await request.json()
        if isinstance(data, dict) and data.get("entry"):
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        from_number = msg.get("from")
                        message_body = None
                        if msg.get("type") == "text":
                            message_body = msg.get("text", {}).get("body")
                        if from_number and message_body:
                            process_whatsapp_reply(from_number, message_body)
                            processed = True
    except Exception:
        # Fall through to attempt Twilio form parsing
        pass

    if not processed:
        try:
            form = await request.form()
            from_number = form.get("From")
            message_body = form.get("Body")
            if from_number and message_body:
                # Twilio numbers come as "whatsapp:+<E.164>"; service normalizes
                process_whatsapp_reply(from_number, message_body)
                processed = True
        except Exception:
            pass

    return {"status": "ok", "processed": processed}


class SendRequest(BaseModel):
    selected_time: Optional[str] = None  # HH:MM
    meal: Optional[str] = None           # breakfast/lunch/dinner
    use_template: Optional[bool] = False
    template_name: Optional[str] = "hello_world"
    template_lang: Optional[str] = "en_US"
    to_override: Optional[str] = None    # optional E.164 to send to directly


def _meal_from_time(selected_time: str) -> str:
    try:
        hour = int(selected_time.split(":")[0])
        if hour < 11:
            return "breakfast"
        elif hour < 16:
            return "lunch"
        else:
            return "dinner"
    except Exception:
        return "breakfast"


@router.post("/send")
def send_mealplan(selected: SendRequest, current_user: str = Depends(decode_access_token)):
    # current_user is email from JWT "sub"
    user_doc = users_col.find_one({"email": {"$regex": f"^{re.escape(current_user)}$", "$options": "i"}})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Require WhatsApp verification before sending
    if not bool(user_doc.get("whatsappVerified")):
        raise HTTPException(status_code=403, detail="Please verify WhatsApp by sending the join message first.")

    # Fetch user's ingredients (stored by email ID in this project)
    ingredients = list(ingredients_col.find({"user_id": current_user}, {"_id": 0, "user_id": 0}))
    if not ingredients:
        raise HTTPException(status_code=400, detail="Add ingredients first")

    # Generate full plan and decide which meal to send
    plan = generate_meal_plan(ingredients) or {}
    if not plan:
        raise HTTPException(status_code=500, detail="Failed to generate meal plan")

    meal_key = (selected.meal or (selected.selected_time and _meal_from_time(selected.selected_time)) or "breakfast").lower()
    if meal_key not in ["breakfast", "lunch", "dinner"]:
        meal_key = "breakfast"

    # Resolve user's timezone for date stamping
    tz_name = user_doc.get("timezone", "UTC")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone("UTC")
    now_local = datetime.now(pytz.utc).astimezone(tz)
    today_str = now_local.date().isoformat()

    # Save plan record (capture insert status for accurate response)
    insert_ok = False
    inserted_id = None
    db_error_msg = None
    try:
        result = mealplans_col.insert_one({
            "user_id": current_user,
            "date": today_str,
            "created_at": datetime.utcnow().isoformat(),
            "origin": "whatsapp_send",
            **plan
        })
        insert_ok = True
        inserted_id = result.inserted_id
    except Exception as e:
        db_error_msg = str(e)
        print(f"Mealplan insert failed: {e}")

    # Validate phone format
    phone = (selected.to_override or user_doc.get("phone") or "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="No phone found. Set your WhatsApp number in Profile.")
    # Require explicit country code with leading '+' (E.164) or 'whatsapp:+<digits>'
    if not re.match(r"^(whatsapp:)?\+\d{7,15}$", phone):
        raise HTTPException(status_code=400, detail="Phone must include country code, e.g., '+91XXXXXXXXXX' or 'whatsapp:+91XXXXXXXXXX'.")

    # Generate and send selected meal via WhatsApp
    filtered_plan = {meal_key: plan.get(meal_key, {})}
    try:
        # If overriding recipient to a number different from profile, prefer template mode unless explicitly disabled
        user_phone = (user_doc.get("phone") or "").strip()
        auto_use_template = False
        if selected.to_override and user_phone and selected.to_override.strip() != user_phone:
            auto_use_template = True

        use_template = bool(selected.use_template) or auto_use_template
        if use_template:
            sid, status, meta_raw = send_template_whatsapp(phone, selected.template_name or "hello_world", selected.template_lang or "en_US")
        else:
            sid, status, meta_raw = send_mealplan_whatsapp(phone, filtered_plan, user_doc.get("name", "User"))
    except Exception as e:
        msg = str(e)
        raise HTTPException(status_code=502, detail=f"WhatsApp send failed: {msg}")

    # On successful send, mark the plan document as sent
    if sid and insert_ok and inserted_id:
        try:
            mealplans_col.update_one({"_id": inserted_id}, {"$set": {"whatsapp_sent_at": datetime.utcnow().isoformat()}})
        except Exception:
            pass

    # Consider success only when Meta/Twilio returns a message id; also report DB status
    is_success = bool(sid)
    return {
        "ok": is_success and insert_ok,
        "db_inserted": insert_ok,
        "db_error": db_error_msg,
        "db_id": str(inserted_id) if inserted_id else None,
        "meal": meal_key,
        "to_number": phone,
        "status": status,
        "message_id": sid,
        "meta_status": status,
        "meta_message_id": sid,
        "meta_raw": meta_raw,
    }

@router.post("/test-scheduler")
async def test_scheduler(current_user: dict = Depends(decode_access_token)):
    """Test endpoint to manually trigger scheduler for current user"""
    from app.services.scheduler import job_send_mealplans
    job_send_mealplans()
    return {"message": "Scheduler triggered manually"}
