import os
from pymongo import MongoClient
import pytz
from datetime import datetime
from pprint import pprint

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['recipe_planner']
EMAIL = os.getenv('TEST_EMAIL', 'sai@gmail.com')

user = db.users.find_one({'email': EMAIL})
if not user:
    print('User not found:', EMAIL)
    raise SystemExit(1)

user_tz = pytz.timezone(user.get('timezone','UTC'))
today = datetime.now(pytz.utc).astimezone(user_tz).date().isoformat()

plans = list(db.meal_plans.find({'user_id': EMAIL, 'date': today}).sort('created_at', -1))
print(f'Today={today} plans count={len(plans)}')
for p in plans:
    info = {k: p.get(k) for k in ['_id','created_at','origin','whatsapp_sent_at']}
    pprint(info)