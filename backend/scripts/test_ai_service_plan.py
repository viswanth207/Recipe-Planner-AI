import os
import sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.services.ai_service import generate_meal_plan

INGREDIENTS = [
    {"name": "Apples", "quantity": 4.0},
    {"name": "Bananas", "quantity": 1.0, "unit": "dozen"},
    {"name": "Biscuits", "quantity": 1.0, "unit": "packet"},
    {"name": "Bread", "quantity": 1.0, "unit": "loaf"},
    {"name": "Chana dal", "quantity": 500.0, "unit": "grams"},
    {"name": "Cornflakes", "quantity": 250.0, "unit": "grams"},
]

if __name__ == "__main__":
    plan = generate_meal_plan(INGREDIENTS)
    import json
    print("===== Generated Meal Plan (JSON) =====")
    print(json.dumps(plan, indent=2, ensure_ascii=False))