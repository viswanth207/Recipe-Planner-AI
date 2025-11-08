import os
from datetime import datetime, timedelta
import pytz
from pymongo import MongoClient

uid = os.getenv('UID','sai@gmail.com')
client = MongoClient(os.getenv('MONGO_URI','mongodb://localhost:27017/'))
db = client['recipe_planner']

user = db.users.find_one({'email': uid})
if not user:
    raise SystemExit('User not found')

user_tz = pytz.timezone(user.get('timezone','Asia/Kolkata'))
now_utc = datetime.now(pytz.utc)
now_user = now_utc.astimezone(user_tz)
next_min = (now_user + timedelta(minutes=1)).replace(second=0, microsecond=0)
new_time = f"{next_min.hour:02d}:{next_min.minute:02d}"
new_date = now_user.date().isoformat()

res = db.users.update_one({'email': uid}, {'$set': {
    'delivery_enabled': True,
    'delivery_date': new_date,
    'delivery_time': new_time
}})
print('Updated:', res.modified_count, 'time=', new_time, 'date=', new_date)