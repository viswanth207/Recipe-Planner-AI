import os
from pymongo import MongoClient
import pytz
from datetime import datetime

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['recipe_planner']

EMAIL = os.getenv('TEST_EMAIL', 'sai@gmail.com')

user = db.users.find_one({'email': EMAIL})
if not user:
    print('User not found:', EMAIL)
    raise SystemExit(1)

user_tz = pytz.timezone(user.get('timezone', 'UTC'))
today = datetime.now(pytz.utc).astimezone(user_tz).date().isoformat()

res = db.meal_plans.update_many({'user_id': EMAIL, 'date': today}, {'$unset': {'whatsapp_sent_at': ''}})
print('Unset whatsapp_sent_at on', res.modified_count, 'document(s) for', EMAIL, 'date', today)