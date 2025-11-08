from fastapi import APIRouter, Depends, HTTPException
try:
    from app.services.gemini_service import generate_meal_plan
except ImportError:
    from app.services.ai_service import generate_meal_plan
from app.database import ingredients_col, mealplans_col, users_col
from app.auth import decode_access_token
from datetime import datetime
import pytz

router = APIRouter(prefix="/mealplan", tags=["mealplan"])

def get_user_id(user_id: str = Depends(decode_access_token)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id

@router.get("/preview")
def preview_mealplan(user_id: str = Depends(decode_access_token)):
    ingredients = list(ingredients_col.find({"user_id": user_id}, {"_id": 0, "user_id": 0}))
    if not ingredients:
        return {"message": "Add ingredients first"}
    
    plan = generate_meal_plan(ingredients)
    return {"meal_plan": plan}

@router.post("/save-now")
def save_mealplan_now(user_id: str = Depends(decode_access_token)):
    # Fetch ingredients
    ingredients = list(ingredients_col.find({"user_id": user_id}, {"_id": 0, "user_id": 0}))
    if not ingredients:
        raise HTTPException(status_code=400, detail="Add ingredients first")

    # Generate plan
    plan = generate_meal_plan(ingredients)
    if not isinstance(plan, dict) or not plan:
        raise HTTPException(status_code=500, detail="Failed to generate meal plan")

    # Resolve user's timezone for date stamping
    user = users_col.find_one({"email": user_id})
    tz_name = (user or {}).get("timezone", "UTC")
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone("UTC")
    now_local = datetime.now(pytz.utc).astimezone(tz)
    today_str = now_local.date().isoformat()

    # Idempotency: avoid duplicate for today
    existing = mealplans_col.find_one({"user_id": user_id, "date": today_str}, {"_id": 0})
    if existing:
        return {"ok": True, "message": "Meal plan already exists for today", "meal_plan": existing}

    # Save
    doc = {
        "user_id": user_id,
        "date": today_str,
        "created_at": datetime.utcnow().isoformat(),
        "origin": "manual_api",
        **plan,
    }
    try:
        mealplans_col.insert_one(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB insert failed: {e}")
    saved = mealplans_col.find_one({"user_id": user_id, "date": today_str}, {"_id": 0})
    return {"ok": True, "message": "Saved", "meal_plan": saved}
