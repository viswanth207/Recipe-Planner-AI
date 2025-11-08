from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date
from pytz import timezone
from app.database import users_col
try:
    from app.services.gemini_service import generate_meal_plan
except ImportError:
    from app.services.ai_service import generate_meal_plan
from app.services.whatsapp_service import send_mealplan_whatsapp, process_whatsapp_reply
import pytz


def job_send_mealplans():
    users = list(users_col.find({"delivery_enabled": True}))
    # Use timezone-aware UTC to avoid naive datetime conversion bugs
    now_utc = datetime.now(pytz.utc)
    for user in users:
        # Safely resolve timezone, defaulting to UTC on invalid entries
        try:
            user_tz = pytz.timezone(user.get("timezone", "UTC"))
        except Exception:
            user_tz = pytz.timezone("UTC")
        now_user = now_utc.astimezone(user_tz)
        
        # Get delivery time and date
        delivery_time = user.get("delivery_time", "08:00")
        delivery_date = user.get("delivery_date")

        # Prerequisite checks: phone and WhatsApp verification
        phone = (user.get("phone") or "").strip()
        whatsapp_verified = bool(user.get("whatsappVerified"))
        if not phone:
            print(f"[Scheduler] Skipping {user.get('email')} — no phone set.")
            continue
        if not whatsapp_verified:
            print(f"[Scheduler] Skipping {user.get('email')} — WhatsApp not verified.")
            continue

        # Debug context for investigation
        try:
            print(f"[Scheduler] User={user.get('email') or str(user.get('_id'))} tz={user.get('timezone','UTC')} now={now_user.strftime('%Y-%m-%d %H:%M')} target={delivery_time} start_date={delivery_date}")
        except Exception:
            pass
        
        try:
            hour, minute = map(int, delivery_time.split(":"))
        except Exception:
            print(f"[Scheduler] Invalid delivery_time for user {user.get('email')}: {delivery_time}")
            continue
            
        # Check if we should send now - works like an alarm
        should_send = False
        using_existing_plan = False
        
        # Respect start date: if a delivery_date is set, only start on/after that date
        try:
            if delivery_date:
                start_date = datetime.strptime(str(delivery_date), "%Y-%m-%d").date()
                if now_user.date() < start_date:
                    # Not yet time to start daily sends
                    print(f"[Scheduler] Skipping user {user.get('email')} until start_date {start_date}")
                    continue
        except Exception:
            # Ignore malformed date and proceed
            print(f"[Scheduler] Malformed delivery_date for user {user.get('email')}: {delivery_date}")
            pass

        # Check if current time matches the delivery time (minute-level)
        if (now_user.hour == hour and now_user.minute == minute):
            # We may send, but confirm idempotency and whether a plan already exists
            from app.database import mealplans_col
            today_str = now_user.date().isoformat()
            user_id = user.get("email") or str(user.get("_id"))
            
            existing_plan = mealplans_col.find_one({
                "user_id": user_id, 
                "date": today_str
            }, sort=[("created_at", -1)])
            
            if existing_plan:
                # If a plan exists, send it unless WhatsApp was already sent
                sent_at = existing_plan.get("whatsapp_sent_at")
                if sent_at:
                    print(f"[Scheduler] Plan exists and WhatsApp already sent for {user_id} on {today_str}; skipping.")
                    should_send = False
                else:
                    print(f"[Scheduler] Using existing plan for {user_id} on {today_str}; will send WhatsApp.")
                    should_send = True
                    using_existing_plan = True
                    plan = existing_plan
            else:
                # No plan yet; we will generate and send
                should_send = True
                using_existing_plan = False
                plan = None
        
        if should_send:
            from app.database import ingredients_col, mealplans_col
            user_id = user.get("email") or str(user.get("_id"))
            if using_existing_plan:
                # Send existing plan via WhatsApp and mark sent
                try:
                    msg_id, status, result = send_mealplan_whatsapp(phone, plan, user.get("name", "User"))
                    print(f"[Scheduler] WhatsApp send status={status} to={phone} msg_id={msg_id}")
                    if plan and plan.get("_id"):
                        mealplans_col.update_one({"_id": plan["_id"]}, {"$set": {"whatsapp_sent_at": datetime.utcnow().isoformat()}})
                    else:
                        mealplans_col.update_one({"user_id": user_id, "date": now_user.date().isoformat()}, {"$set": {"whatsapp_sent_at": datetime.utcnow().isoformat()}})
                    if result and result.get('status') == 'error':
                        print(f"[Scheduler] Twilio error response: {result.get('response') or result.get('message')} payload={result.get('payload')}")
                except Exception as e:
                    print(f"[Scheduler] Exception during WhatsApp send for {user_id}: {e}")
                continue

            # Generate meal plan
            ingredients = list(ingredients_col.find({"user_id": user_id}, {"_id":0, "user_id":0}))
            if ingredients:
                try:
                    plan = generate_meal_plan(ingredients)
                except Exception as e:
                    print(f"[Scheduler] Meal plan generation failed for {user_id}: {e}")
                    continue
                # Save plan
                try:
                    insert_result = mealplans_col.insert_one({
                        "user_id": user_id,
                        "date": now_user.date().isoformat(),
                        "created_at": datetime.utcnow().isoformat(),
                        "origin": "scheduler",
                        **plan
                    })
                    saved_doc = mealplans_col.find_one({"_id": insert_result.inserted_id}, {"_id":0})
                    if saved_doc:
                        import json as _json
                        print("[SOURCE: MongoDB meal_plans | Gemini AI] Saved plan:", _json.dumps(saved_doc, ensure_ascii=False))
                except Exception as e:
                    print(f"[Scheduler] Failed to save plan for {user_id}: {e}")
                # Send via WhatsApp (Meta Cloud)
                try:
                    msg_id, status, result = send_mealplan_whatsapp(phone, plan, user.get("name", "User"))
                    print(f"[Scheduler] WhatsApp send status={status} to={phone} msg_id={msg_id}")
                    mealplans_col.update_one({"_id": insert_result.inserted_id}, {"$set": {"whatsapp_sent_at": datetime.utcnow().isoformat()}})
                    if result and result.get('status') == 'error':
                        print(f"[Scheduler] Twilio error response: {result.get('response') or result.get('message')} payload={result.get('payload')}")
                except Exception as e:
                    print(f"[Scheduler] Exception during WhatsApp send for {user_id}: {e}")
            else:
                print(f"[Scheduler] No ingredients for user {user_id}; not generating plan.")


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Run every 10 seconds to achieve near "alarm clock" immediacy
    scheduler.add_job(job_send_mealplans, 'interval', seconds=10)
    scheduler.start()
    print("Scheduler started...")
