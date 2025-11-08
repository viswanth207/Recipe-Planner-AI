import openai
from app.config import OPENAI_API_KEY
import os

openai.api_key = OPENAI_API_KEY

# Sampling config to increase variety in fallback
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.9"))
OPENAI_TOP_P = float(os.getenv("OPENAI_TOP_P", "0.95"))
OPENAI_PRESENCE_PENALTY = float(os.getenv("OPENAI_PRESENCE_PENALTY", "0.3"))
OPENAI_FREQUENCY_PENALTY = float(os.getenv("OPENAI_FREQUENCY_PENALTY", "0.2"))

# --- Helpers to ensure realistic recipes even if model output is imperfect ---

def _normalize_ingredients(ingredients):
    normalized = []
    for ing in (ingredients or []):
        name = str(ing.get('name', '')).strip()
        qty = ing.get('quantity')
        unit = ing.get('unit')
        if isinstance(unit, str) and unit.lower() == 'dozen' and isinstance(qty, (int, float)):
            qty = float(qty) * 12
            unit = 'pieces'
        normalized.append({'name': name or 'Unknown', 'quantity': qty, 'unit': unit})
    return normalized


def _sanitize_steps(steps, ingredients):
    if not steps:
        return []
    lower_names = [(ing.get('name') or '').lower() for ing in (ingredients or [])]
    packaged = set(['biscuits', 'cornflakes', 'bread', 'maggi', 'papad', 'tomato ketchup', 'peanut butter'])
    dals = set(['chana dal', 'toor dal', 'moong dal', 'masoor dal', 'rajma'])
    equipment_terms = ['cutting board', 'knife', 'mixing bowl', 'pot', 'pan', 'spatula', 'strainer', 'colander']

    def fix_line(line):
        s = str(line).strip()
        ls = s.lower()
        # Remove equipment-list/setup lines
        eq_count = sum(1 for term in equipment_terms if term in ls)
        if ls.startswith('set out') or 'prepare your workspace' in ls or eq_count >= 3:
            return ''
        # Specific corrections
        if 'wash and chop cornflakes' in ls:
            return 'Use cornflakes as a crunchy topping; do not chop.'
        if 'wash and chop bread' in ls:
            return 'Toast bread slices until golden; cut into pieces.'
        if 'wash and chop chana dal' in ls:
            return 'Rinse chana dal; boil until tender; season to taste.'
        # Generic corrections
        for name in lower_names:
            if name in packaged and ('wash' in ls and ('chop' in ls or 'dice' in ls) and name in ls):
                if name == 'biscuits':
                    return 'Crush biscuits into coarse crumbs.'
                if name == 'cornflakes':
                    return 'Use cornflakes as a crunchy topping; do not chop.'
                if name == 'bread':
                    return 'Toast bread slices until golden; cut into triangles.'
                if name == 'maggi':
                    return 'Cook Maggi noodles as per packet instructions.'
                if name == 'papad':
                    return 'Roast or fry papad until crisp.'
            if name in dals and ('chop' in ls and name in ls):
                return f'Rinse {name}; boil until tender and season.'
            if name in ['banana', 'bananas'] and 'chop' in ls and name in ls:
                return 'Peel and slice bananas.'
        return s

    cleaned = []
    for line in steps:
        fixed = fix_line(line)
        if fixed:
            cleaned.append(fixed)
    # Deduplicate while preserving order; cap to 10 steps
    seen = set()
    unique = []
    for s in cleaned:
        if s not in seen:
            seen.add(s)
            unique.append(s)
    return unique[:10]


def _sanitize_recipe(recipe: dict) -> dict:
    r = dict(recipe or {})
    ingredients = r.get('ingredients_used') or r.get('ingredients') or []
    r['ingredients_used'] = _normalize_ingredients(ingredients)
    r['steps'] = _sanitize_steps(r.get('steps') or [], r['ingredients_used'])
    return r


def _fallback_plan(ingredients: list) -> dict:
    # Simple rule-based plan using only the user's actual ingredients
    names = {str(i.get('name','')).lower(): i for i in (ingredients or [])}
    all_names = list(names.keys())
    has = lambda k: any(k == n for n in names.keys())

    def q(n):
        # Return the actual ingredient dict only if present
        return names.get(n)

    def present(list_of_names):
        return [q(n) for n in list_of_names if has(n)]

    fruits_list = ['apple','apples','banana','bananas','orange','oranges','mango','mangos','grape','grapes','pear','pears']
    dal_list = ['chana dal','toor dal','moong dal','masoor dal','rajma']
    fruits_present = [n for n in all_names if n in fruits_list]
    bread_present = [n for n in all_names if n in ['bread']]
    dal_present = [n for n in all_names if n in dal_list]

    # Breakfast
    if has('cornflakes'):
        breakfast_ing = [q('cornflakes')] + [names[n] for n in fruits_present]
        breakfast_ing = [i for i in breakfast_ing if i]
        breakfast = {
            'recipe_name': 'Cornflakes Fruit Bowl' if fruits_present else 'Cornflakes Bowl',
            'ingredients_used': breakfast_ing,
            'steps': [
                'Slice any available fruit (e.g., banana, apple).',
                'In a bowl, add cornflakes and fruit.',
                'Optional: drizzle honey; serve immediately.'
            ],
            'prep_time': '5–10 min', 'cook_time': '0 min', 'calories': '300-400',
            'youtube_link': 'https://www.youtube.com/results?search_query=cornflakes+fruit+bowl'
        }
    else:
        # Prefer toast + fruit if available, otherwise toast only or fruit only
        bf_ing = [names[n] for n in bread_present] + [names[n] for n in fruits_present]
        bf_ing = [i for i in bf_ing if i]
        if bread_present and fruits_present:
            breakfast = {
                'recipe_name': 'Fruit and Toast',
                'ingredients_used': bf_ing,
                'steps': [
                    'Toast bread slices until golden; cut into pieces.',
                    'Wash and slice available fruit; serve alongside.'
                ],
                'prep_time': '10 min', 'cook_time': '5 min', 'calories': '300-400',
                'youtube_link': 'https://www.youtube.com/results?search_query=fruit+and+toast+breakfast'
            }
        elif bread_present:
            breakfast = {
                'recipe_name': 'Simple Toast',
                'ingredients_used': [names[bread_present[0]]],
                'steps': [
                    'Toast bread slices until golden (1–2 minutes per side).',
                    'Optional: add butter or oil for flavor.'
                ],
                'prep_time': '5 min', 'cook_time': '5 min', 'calories': '200-300',
                'youtube_link': 'https://www.youtube.com/results?search_query=how+to+toast+bread'
            }
        elif fruits_present:
            breakfast = {
                'recipe_name': 'Simple Fruit Plate',
                'ingredients_used': [names[n] for n in fruits_present],
                'steps': [
                    'Wash and slice available fruit.',
                    'Optional: drizzle a few drops of lemon to prevent browning.'
                ],
                'prep_time': '5–10 min', 'cook_time': '0 min', 'calories': '150-250',
                'youtube_link': 'https://www.youtube.com/results?search_query=simple+fruit+plate'
            }
        else:
            # Generic breakfast using first few items present
            some = [names[n] for n in all_names[:3]]
            some = [i for i in some if i]
            breakfast = {
                'recipe_name': 'Simple Breakfast Plate',
                'ingredients_used': some,
                'steps': [
                    'Prepare available items appropriately: wash, peel, chop, or toast as needed.',
                    'Combine on a plate; season lightly; serve.'
                ],
                'prep_time': '10 min', 'cook_time': '0–10 min', 'calories': '200-400',
                'youtube_link': 'https://www.youtube.com/results?search_query=simple+breakfast+plate'
            }

    # Lunch
    if has('biscuits') and not dal_present:
        lunch_ing = [q('biscuits')] + ([names[fruits_present[0]]] if fruits_present else [])
        lunch_ing = [i for i in lunch_ing if i]
        lunch = {
            'recipe_name': 'Simple Biscuit Snack Plate' if fruits_present else 'Biscuit Plate',
            'ingredients_used': lunch_ing,
            'steps': [
                'Serve biscuits whole or lightly crush into coarse crumbs.',
                'Slice any available fruit; serve alongside.'
            ],
            'prep_time': '5 min', 'cook_time': '0 min', 'calories': '200-350',
            'youtube_link': 'https://www.youtube.com/results?search_query=biscuit+snack+plate'
        }
    elif dal_present:
        dal_name = dal_present[0]
        lunch = {
            'recipe_name': 'Simple Dal Bowl',
            'ingredients_used': [names[dal_name]],
            'steps': [
                f'Rinse {dal_name} thoroughly.',
                'Boil in water until tender (30–40 min); salt to taste.',
                'Optional: temper with oil and spices if available.'
            ],
            'prep_time': '10 min', 'cook_time': '40 min', 'calories': '350-450',
            'youtube_link': 'https://www.youtube.com/results?search_query=chana+dal+recipe'
        }
    else:
        some = [names[n] for n in all_names[:3]]
        some = [i for i in some if i]
        lunch = {
            'recipe_name': 'Simple Lunch Plate',
            'ingredients_used': some,
            'steps': [
                'Prepare available items appropriately: wash, peel, chop, or sauté as needed.',
                'Combine on a plate or bowl; season lightly; serve.'
            ],
            'prep_time': '10 min', 'cook_time': '0–15 min', 'calories': '250-450',
            'youtube_link': 'https://www.youtube.com/results?search_query=simple+lunch+plate'
        }

    # Dinner
    if dal_present:
        dal_name = dal_present[0]
        dinner_ing = [names[dal_name]] + ([names[bread_present[0]]] if bread_present else []) + ([names[fruits_present[0]]] if fruits_present else [])
        dinner_ing = [i for i in dinner_ing if i]
        dinner = {
            'recipe_name': 'Dal Bowl with Toast' if bread_present else 'Simple Dal Bowl',
            'ingredients_used': dinner_ing,
            'steps': [
                f'Rinse {dal_name} and boil until tender; season to taste.',
                'Toast bread slices; cut into triangles.' if bread_present else 'Optional: serve with toast if available.',
                'Optional: serve fruit slices on the side.' if fruits_present else 'Optional: garnish as preferred.'
            ],
            'prep_time': '10 min', 'cook_time': '40 min', 'calories': '400-550',
            'youtube_link': 'https://www.youtube.com/results?search_query=chana+dal+simple+recipe'
        }
    else:
        dn_ing = [names[n] for n in bread_present + fruits_present]
        dn_ing = [i for i in dn_ing if i]
        if bread_present and fruits_present:
            dinner = {
                'recipe_name': 'Toast with Fruit',
                'ingredients_used': dn_ing,
                'steps': [
                    'Toast bread; cut into pieces.',
                    'Wash and slice available fruit; serve alongside.'
                ],
                'prep_time': '10 min', 'cook_time': '5 min', 'calories': '300-450',
                'youtube_link': 'https://www.youtube.com/results?search_query=toast+with+fruit'
            }
        else:
            some = [names[n] for n in all_names[:3]]
            some = [i for i in some if i]
            dinner = {
                'recipe_name': 'Simple Dinner Bowl',
                'ingredients_used': some,
                'steps': [
                    'Prepare available items appropriately: wash, peel, chop, or sauté as needed.',
                    'Combine in a bowl; season lightly; serve warm.'
                ],
                'prep_time': '10 min', 'cook_time': '0–15 min', 'calories': '300-500',
                'youtube_link': 'https://www.youtube.com/results?search_query=simple+dinner+bowl'
            }

    # Sanitize before returning
    return {
        'breakfast': _sanitize_recipe(breakfast),
        'lunch': _sanitize_recipe(lunch),
        'dinner': _sanitize_recipe(dinner),
    }


def generate_meal_plan(ingredients: list):
    """
    Generate a structured meal plan using OpenAI GPT-4 Turbo with constraints.
    If the model output is missing/invalid or the API fails, use a rule-based fallback.
    ingredients: list of dicts [{"name": "", "quantity": 0, "unit": ""}, ...]
    Returns a dict with breakfast, lunch, dinner
    """
    ingredient_list = "\n".join([f"{i.get('name','')}: {i.get('quantity')} {i.get('unit') or ''}" for i in ingredients])

    prompt = f"""
    You are a culinary assistant. Use ONLY the provided ingredients (minor pantry staples like water, salt, oil are OK).
    Return a healthy one-day meal plan with Breakfast, Lunch, and Dinner.
    Constraints:
    - Steps must be realistic: DO NOT suggest chopping cereals, packaged foods, or legumes.
    - Handle items correctly:
      * Bread → toast and cut; do not wash or chop raw bread.
      * Cornflakes → use as ready-to-eat topping; do not chop.
      * Biscuits → serve whole or crush; do not chop.
      * Chana dal (and dals) → rinse, boil until tender, season; do not chop.
      * Bananas → peel and slice.
    - Keep steps concise (max 8 per recipe), avoid equipment listing/setup lines.
    - Prefer savory dinner; avoid breakfast-style cereal as main dinner.
    - Include realistic prep_time, cook_time, calories.
    - Include a YouTube link that demonstrates a similar recipe.

    Ingredients:\n{ingredient_list}

    Return EXACT JSON with keys: breakfast, lunch, dinner. Each value is:
    {{
      "recipe_name": "",
      "ingredients_used": [{{"name": "", "quantity": 0, "unit": ""}}],
      "steps": [],
      "prep_time": "",
      "cook_time": "",
      "calories": "",
      "youtube_link": ""
    }}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=OPENAI_TEMPERATURE,
            top_p=OPENAI_TOP_P,
            presence_penalty=OPENAI_PRESENCE_PENALTY,
            frequency_penalty=OPENAI_FREQUENCY_PENALTY,
            max_tokens=900
        )
        plan_text = response['choices'][0]['message']['content']
        import json
        plan_json = json.loads(plan_text)
        # Sanitize each recipe to guarantee correctness
        for key in ['breakfast','lunch','dinner']:
            if isinstance(plan_json.get(key), dict):
                plan_json[key] = _sanitize_recipe(plan_json[key])
        return plan_json
    except Exception as e:
        print("AI service error, using fallback:", e)
        return _fallback_plan(ingredients)
