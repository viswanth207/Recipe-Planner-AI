import os
from pymongo import MongoClient

uri = os.getenv('MONGO_URI','mongodb://localhost:27017/')
client = MongoClient(uri)
db = client['recipe_planner']

print('\n=== Users with delivery_enabled ===')
for u in db.users.find({'delivery_enabled': True}, {'_id':0, 'email':1, 'phone':1, 'timezone':1, 'delivery_time':1, 'delivery_date':1, 'whatsappVerified':1}):
    print(u)

print('\n=== All users (key scheduling fields) ===')
for u in db.users.find({}, {'_id':0, 'email':1, 'phone':1, 'timezone':1, 'delivery_time':1, 'delivery_date':1, 'delivery_enabled':1, 'whatsappVerified':1}):
    print(u)

print('\n=== Ingredients per user (counts) ===')
for u in db.users.find({}, {'_id':0, 'email':1}):
    uid = u['email']
    c = db.ingredients.count_documents({'user_id': uid})
    print(f"{uid}: {c} ingredients")

print('\n=== Latest 3 meal plans by user ===')
for uid_doc in db.users.find({}, {'_id':0, 'email':1}):
    uid = uid_doc['email']
    plans = list(db.meal_plans.find({'user_id': uid}).sort('date', -1).limit(3))
    if plans:
        print(f"\n{uid} -> {len(plans)} plans:")
        for p in plans:
            print({k:p.get(k) for k in ['date','origin']})
    else:
        print(f"\n{uid} -> no plans")