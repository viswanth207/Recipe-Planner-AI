import os
from datetime import datetime, timedelta
import pytz
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["recipe_planner"]

EMAIL = os.getenv("TEST_EMAIL", "sai@gmail.com")

user = db.users.find_one({"email": EMAIL})
if not user:
    print("User not found:", EMAIL)
    raise SystemExit(1)

# Compute next minute in user's timezone
user_tz = pytz.timezone(user.get("timezone", "Asia/Kolkata"))
now_local = datetime.now(pytz.utc).astimezone(user_tz)
next_minute = (now_local + timedelta(minutes=1)).replace(second=0, microsecond=0)
new_time = f"{next_minute.hour:02d}:{next_minute.minute:02d}"
new_date = now_local.date().isoformat()

# Update user delivery settings
res_user = db.users.update_one(
    {"email": EMAIL},
    {"$set": {
        "delivery_enabled": True,
        "delivery_date": new_date,
        "delivery_time": new_time,
    }}
)

# Clear whatsapp_sent_at on today's latest plan in meal_plans
latest_plan = db.meal_plans.find_one(
    {"user_id": EMAIL, "date": new_date},
    sort=[("created_at", -1)]
)

if latest_plan:
    db.meal_plans.update_one({"_id": latest_plan["_id"]}, {"$unset": {"whatsapp_sent_at": ""}})
    print(f"Prepared: email={EMAIL} time={new_time} date={new_date}; cleared whatsapp_sent_at")
else:
    print(f"Prepared: email={EMAIL} time={new_time} date={new_date}; no existing plan to clear")