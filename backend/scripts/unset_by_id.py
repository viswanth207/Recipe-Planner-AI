import os
from pymongo import MongoClient
from bson import ObjectId

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['recipe_planner']

PLAN_ID = os.getenv('PLAN_ID')
if not PLAN_ID:
    print('PLAN_ID env is required, e.g., set PLAN_ID=68f25eab06535160914a49c6')
    raise SystemExit(1)

res = db.meal_plans.update_one({'_id': ObjectId(PLAN_ID)}, {'$unset': {'whatsapp_sent_at': ''}})
print('Unset whatsapp_sent_at modified_count=', res.modified_count)