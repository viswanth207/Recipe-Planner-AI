from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import re
import pytz

from app.auth import decode_access_token
from app.database import ingredients_col, mealplans_col, users_col
try:
    from app.services.gemini_service import generate_meal_plan
except ImportError:
    from app.services.ai_service import generate_meal_plan
from app.services.whatsapp_service import send_mealplan_whatsapp

router = APIRouter(prefix="/agentic", tags=["agentic"])  # New orchestration endpoints


class IngredientIn(BaseModel):
    name: str
    quantity: float = Field(ge=0)
    unit: str

class AgenticRunRequest(BaseModel):
    ingredients: Optional[List[IngredientIn]] = None
    send_now: Optional[bool] = False
    delivery_time: Optional[str] = None   # HH:MM
    delivery_date: Optional[str] = None   # YYYY-MM-DD
    delivery_enabled: Optional[bool] = None
    timezone: Optional[str] = None
    meal: Optional[str] = None            # breakfast/lunch/dinner
    to_override: Optional[str] = None


@router.post("/run")
def run_agentic_flow(payload: AgenticRunRequest, current_user: str = Depends(decode_access_token)):
    # 1) Upsert provided ingredients
    if payload.ingredients:
        for ing in payload.ingredients:
            ingredients_col.update_one(
                {"user_id": current_user, "name": ing.name},
                {"$set": {"name": ing.name, "quantity": float(ing.quantity), "unit": ing.unit, "user_id": current_user}},
                upsert=True
            )

    # 2) Fetch ingredients to use for planning
    ingredients = list(ingredients_col.find({"user_id": current_user}, {"_id": 0, "user_id": 0}))
    if not ingredients:
        raise HTTPException(status_code=400, detail="Add ingredients first")

    # 3) Generate meal plan via Gemini (with built-in fallbacks)
    plan = generate_meal_plan(ingredients)
    if not isinstance(plan, dict) or not plan:
        raise HTTPException(status_code=500, detail="Failed to generate meal plan")

    # 4) Resolve timezone for date stamping
    user_doc = users_col.find_one({"email": {"$regex": f"^{re.escape(current_user)}$", "$options": "i"}})
    tz_name = (user_doc or {}).get("timezone", payload.timezone or "UTC")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone("UTC")
    now_local = datetime.now(pytz.utc).astimezone(tz)
    today_str = now_local.date().isoformat()

    # 5) Save plan (idempotent for the day)
    existing = mealplans_col.find_one({"user_id": current_user, "date": today_str}, {"_id": 0})
    inserted_id = None
    if existing:
        saved_doc = existing
    else:
        doc = {
            "user_id": current_user,
            "date": today_str,
            "created_at": datetime.utcnow().isoformat(),
            "origin": "agentic_api",
            **plan,
        }
        try:
            res = mealplans_col.insert_one(doc)
            inserted_id = res.inserted_id
            saved_doc = mealplans_col.find_one({"user_id": current_user, "date": today_str}, {"_id": 0})
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")

    # 6) Optionally update delivery preferences on profile
    schedule_updates = {}
    if payload.delivery_time is not None:
        t = (payload.delivery_time or '').strip()
        if not re.match(r"^\d{2}:\d{2}$", t):
            raise HTTPException(status_code=400, detail="delivery_time must be HH:MM")
        try:
            datetime.strptime(t, "%H:%M")
        except ValueError:
            raise HTTPException(status_code=400, detail="delivery_time invalid")
        schedule_updates["delivery_time"] = t
    if payload.delivery_date is not None:
        d = (payload.delivery_date or '').strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            raise HTTPException(status_code=400, detail="delivery_date must be YYYY-MM-DD")
        try:
            datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="delivery_date invalid")
        schedule_updates["delivery_date"] = d
    if payload.delivery_enabled is not None:
        schedule_updates["delivery_enabled"] = bool(payload.delivery_enabled)
    if payload.timezone is not None:
        tz_in = (payload.timezone or '').strip()
        try:
            pytz.timezone(tz_in)
        except Exception:
            raise HTTPException(status_code=400, detail="timezone must be valid IANA tz")
        schedule_updates["timezone"] = tz_in
    if schedule_updates:
        users_col.update_one(
            {"email": {"$regex": f"^{re.escape(current_user)}$", "$options": "i"}},
            {"$set": schedule_updates}
        )

    # 7) Decide meal to send and auto-send if current time matches schedule
    send_result = None
    msg_id = None
    meal_key = (payload.meal or "").lower()
    if meal_key not in ["breakfast", "lunch", "dinner"]:
        # Fall back to mapped meal by delivery_time, else breakfast
        effective_time = schedule_updates.get("delivery_time") or (payload.delivery_time or (user_doc or {}).get("delivery_time"))
        if effective_time:
            try:
                hour = int(effective_time.split(":")[0])
                meal_key = "breakfast" if hour < 11 else ("lunch" if hour < 16 else "dinner")
            except Exception:
                meal_key = "breakfast"
        else:
            meal_key = "breakfast"

    # Compute auto send (if send_now not explicitly requested)
    auto_triggered = False
    send_now_flag = bool(payload.send_now)
    if not send_now_flag:
        try:
            delivery_enabled = schedule_updates.get("delivery_enabled", bool((user_doc or {}).get("delivery_enabled")))
            delivery_time = schedule_updates.get("delivery_time", (user_doc or {}).get("delivery_time"))
            delivery_date = schedule_updates.get("delivery_date", (user_doc or {}).get("delivery_date"))
            if delivery_enabled and delivery_time:
                hour, minute = map(int, delivery_time.split(":"))
                # Respect start date if set
                allow_date = True
                if delivery_date:
                    try:
                        start_date = datetime.strptime(str(delivery_date), "%Y-%m-%d").date()
                        allow_date = now_local.date() >= start_date
                    except Exception:
                        allow_date = True
                # Tolerate ±1 minute to prevent race with minute boundary
                if allow_date:
                    now_total = now_local.hour * 60 + now_local.minute
                    target_total = hour * 60 + minute
                    if abs(now_total - target_total) <= 1:
                        send_now_flag = True
                        auto_triggered = True
        except Exception:
            pass

    if send_now_flag:
        # Require WhatsApp verification and phone set
        if not bool((user_doc or {}).get("whatsappVerified")):
            raise HTTPException(status_code=403, detail="Please verify WhatsApp first.")
        phone = (payload.to_override or (user_doc or {}).get("phone") or '').strip()
        if not phone:
            raise HTTPException(status_code=400, detail="No phone found on profile. Set your WhatsApp number.")
        if not re.match(r"^(whatsapp:)?\+\d{7,15}$", phone):
            raise HTTPException(status_code=400, detail="Phone must include country code, e.g., '+91XXXXXXXXXX' or 'whatsapp:+91XXXXXXXXXX'.")
        filtered_plan = {meal_key: plan.get(meal_key, {})}
        try:
            sid, status, send_result = send_mealplan_whatsapp(phone, filtered_plan, (user_doc or {}).get("name", "User"))
            msg_id = sid
            if sid:
                # Mark WhatsApp sent for today's plan regardless of insert path
                try:
                    mealplans_col.update_one({"user_id": current_user, "date": today_str}, {"$set": {"whatsapp_sent_at": datetime.utcnow().isoformat()}})
                except Exception:
                    pass
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"WhatsApp send failed: {e}")

    return {
        "ok": True,
        "meal_key": meal_key,
        "db_id": str(inserted_id) if inserted_id else None,
        "db_saved": bool(inserted_id or existing),
        "scheduled_updates": schedule_updates,
        "whatsapp_sent": bool(msg_id),
        "whatsapp_message_id": msg_id,
        "whatsapp_meta": send_result,
        "auto_sent": auto_triggered,
        "meal_plan": saved_doc,
    }