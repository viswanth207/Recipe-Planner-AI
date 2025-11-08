import json
import sys
from pathlib import Path

# Ensure we can import app.services
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
sys.path.append(str(ROOT / "app"))

from app.services.gemini_service import generate_meal_plan

INGREDIENTS = [
    {"name": "apples", "quantity": 2, "unit": "pieces"},
    {"name": "bananas", "quantity": 2, "unit": "pieces"},
    {"name": "biscuits", "quantity": 100, "unit": "g"},
    {"name": "bread", "quantity": 4, "unit": "slices"},
    {"name": "chana dal", "quantity": 200, "unit": "g"},
    {"name": "cornflakes", "quantity": 200, "unit": "g"},
]

if __name__ == "__main__":
    plan = generate_meal_plan(INGREDIENTS)
    print(json.dumps(plan, indent=2, ensure_ascii=False))