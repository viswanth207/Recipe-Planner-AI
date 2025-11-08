from pymongo import MongoClient
from pymongo import ASCENDING
from app.config import MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client.recipe_planner  # Explicitly specify database name

users_col = db['users']
ingredients_col = db['ingredients']
mealplans_col = db['meal_plans']


def init_indexes():
    """Create indexes to improve query performance. Safe to call multiple times."""
    try:
        # Users: fast lookup by email (case normalized to lowercase at signup)
        users_col.create_index([("email", ASCENDING)], name="idx_users_email")
    except Exception:
        pass
    try:
        # Ingredients: speed up per-user queries and updates by name
        ingredients_col.create_index([("user_id", ASCENDING), ("name", ASCENDING)], name="idx_ingredients_user_name")
    except Exception:
        pass
    try:
        # Meal plans: support scheduler lookups and daily idempotency
        mealplans_col.create_index([("user_id", ASCENDING), ("date", ASCENDING)], name="idx_mealplans_user_date")
        mealplans_col.create_index([("created_at", ASCENDING)], name="idx_mealplans_created_at")
    except Exception:
        pass
