import os
from pymongo import MongoClient
from pprint import pprint
from datetime import datetime
import pytz

uid = os.getenv('UID','sai@gmail.com')
uri = os.getenv('MONGO_URI','mongodb://localhost:27017/')
client = MongoClient(uri)
db = client['recipe_planner']

user = db.users.find_one({'email': uid}, {'_id':0})
print('User doc (key scheduling fields):')
print({k: user.get(k) for k in ['email','phone','timezone','delivery_enabled','delivery_date','delivery_time','whatsappVerified']})

user_tz = pytz.timezone(user.get('timezone','UTC'))
now_utc = datetime.now(pytz.utc)
today_str = now_utc.astimezone(user_tz).date().isoformat()
print('\nToday:', today_str)
plan = db.meal_plans.find_one({'user_id': uid, 'date': today_str}, {'_id':0})

if plan:
    print('Found plan metadata:')
    meta = {k: plan.get(k) for k in ['date','created_at','origin']}
    print(meta)
else:
    print('No plan found for today')