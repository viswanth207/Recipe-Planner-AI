import os
import sys

# Ensure 'backend' root is on the Python path for `import app...`
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from app.services.whatsapp_service import WhatsAppService

# Construct a sample plan using the problematic example provided
sample_recipe = {
    "recipe_name": "Simple Dinner Bowl",
    "ingredients": [
        {"name": "Apples", "quantity": 4.0},
        {"name": "Bananas", "quantity": 1.0, "unit": "dozen"},
        {"name": "Biscuits", "quantity": 1.0, "unit": "packet"},
        {"name": "Bread", "quantity": 1.0, "unit": "loaf"},
        {"name": "Chana dal", "quantity": 500.0, "unit": "grams"},
        {"name": "Cornflakes", "quantity": 250.0, "unit": "grams"},
    ],
    "steps": [
        "Set out a cutting board, knife, mixing bowl, pot, pan, spatula, and strainer.",
        "Wash and chop 4.0 apples on a cutting board.",
        "Wash and chop 1.0 dozen bananas on a cutting board.",
        "Wash and chop 1.0 packet biscuits on a cutting board.",
        "Wash and chop 1.0 loaf bread on a cutting board.",
        "Wash and chop 500.0 grams chana dal on a cutting board.",
        "Wash and chop 250.0 grams cornflakes on a cutting board.",
        "Season with a pinch of salt and pepper. Taste and adjust seasoning.",
        "Serve warm. Garnish with chopped herbs if available. Enjoy!",
        "Clean workspace and organize leftovers in airtight containers for later use.",
    ],
    "youtube_link": "https://www.youtube.com/results?search_query=Simple+Dinner+Bowl+easy+recipe",
}

meal_plan_payload = {
    "user_name": "sai",
    "dinner": sample_recipe,
}

if __name__ == "__main__":
    svc = WhatsAppService()
    formatted = svc.format_meal_plan_message(meal_plan_payload)
    print("===== Sanitized WhatsApp Message Preview =====")
    print(formatted)