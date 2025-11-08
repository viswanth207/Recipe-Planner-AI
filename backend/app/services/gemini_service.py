import os
import json
import requests
from urllib.parse import quote_plus
from dotenv import load_dotenv
from app.services.ai_service import generate_meal_plan as openai_generate_meal_plan
from app.services.beginner_mode import apply_beginner_mode, BEGINNER_MODE

# Load environment to pick up latest .env values without full server restart
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
DEFAULT_ENDPOINT_VERSION = os.getenv("GEMINI_API_VERSION", "v1beta")
# Add config for generation randomness
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.9"))
GEMINI_TOP_P = float(os.getenv("GEMINI_TOP_P", "0.95"))
GEMINI_TOP_K = int(os.getenv("GEMINI_TOP_K", "40"))

def parse_voice_intent(text: str):
    """
    Very lightweight local intent parser for voice commands related to ingredients
    and delivery preferences. Returns a dict {"type": ..., "payload": {...}}.
    """
    t = (text or "").strip().lower()
    # add ingredient: "add 2 kg rice" or "add 3 tomatoes"
    import re
    m = re.match(r"^add\s+(\d+(?:\.\d+)?)\s*(\w+)?\s+([a-zA-Z ]+)$", t)
    if m:
        quantity = float(m.group(1))
        unit = (m.group(2) or "").strip()
        name = (m.group(3) or "").strip()
        return {"type": "add_ingredient", "payload": {"name": name, "quantity": quantity, "unit": unit}}

    m = re.match(r"^(delete|remove)\s+(?:ingredient\s+)?([a-zA-Z ]+)$", t)
    if m:
        name = (m.group(2) or "").strip()
        return {"type": "delete_ingredient", "payload": {"name": name}}

    m = re.match(r"^(?:set\s+)?delivery\s+(?:time\s+)?(?:to|at)\s+(.+)$", t)
    if m:
        time_str = m.group(1).strip()
        # normalize to HH:MM if possible
        hhmm = re.search(r"\b(\d{1,2}):(\d{2})\b", time_str)
        if hhmm:
            h = int(hhmm.group(1)); mni = int(hhmm.group(2))
            if 0 <= h <= 23 and 0 <= mni <= 59:
                return {"type": "set_delivery_time", "payload": {"delivery_time": f"{h:02d}:{mni:02d}"}}
        ampm = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", time_str)
        if ampm:
            h = int(ampm.group(1)); mni = int(ampm.group(2) or 0); ap = ampm.group(3)
            if h == 12: h = 0
            if ap == "pm": h += 12
            if 0 <= h <= 23 and 0 <= mni <= 59:
                return {"type": "set_delivery_enabled", "payload": {"delivery_enabled": True}}
    if "enable delivery" in t or "turn on delivery" in t:
        return {"type": "set_delivery_enabled", "payload": {"delivery_enabled": True}}
    if "disable delivery" in t or "turn off delivery" in t:
        return {"type": "set_delivery_enabled", "payload": {"delivery_enabled": False}}

    return {"type": "unknown"}

def _basic_meal_plan(ingredients: list):
    def _sanitize(ing: dict):
        return {
            "name": str(ing.get("name", "")),
            "quantity": float(ing.get("quantity", 0) or 0),
            "unit": str(ing.get("unit", "")),
        }

    def _title_from(used_names: set, meal_label: str) -> str:
        has_rice = any(n in used_names for n in ["rice"])
        has_chicken = any(n in used_names for n in ["chicken"])
        has_eggs = any(n in used_names for n in ["egg", "eggs"])
        has_tomato = any(n in used_names for n in ["tomato", "tomatoes"])
        if has_chicken and has_rice:
            return f"Hearty Chicken & Rice {meal_label.capitalize()} Bowl"
        if has_eggs and has_tomato:
            return f"Egg & Tomato {meal_label.capitalize()} Skillet"
        return f"Simple {meal_label.capitalize()} Bowl"

    def _prep_step(ing: dict) -> str:
        name = (ing.get("name") or "").lower().strip()
        qty = ing.get("quantity") or ""
        unit = ing.get("unit") or ""
        q = f"{qty} {unit}".strip()
        if name in ["rice"]:
            return f"Rinse {q} rice in a strainer for 60 seconds, then set aside."
        if name in ["chicken"]:
            return f"Cut {q} chicken into bite-sized pieces on a cutting board."
        if name in ["egg", "eggs"]:
            return f"Crack {qty} egg(s) into a bowl and whisk vigorously for 30 seconds."
        if name in ["tomato", "tomatoes"]:
            return f"Wash {q} tomatoes and dice into 1 cm pieces using a knife."
        if name in ["chilli", "chili", "chilies", "chiles"]:
            return f"Slice {q} chili thinly; remove seeds if sensitive to heat."
        return f"Wash and chop {q} {name} on a cutting board."

    def _meal(meal_label: str):
        used_raw = ingredients[:min(6, len(ingredients))]
        used = [_sanitize(x) for x in used_raw]
        names_lower = { (u.get("name") or "").lower().strip() for u in used }
        has_rice = "rice" in names_lower
        has_chicken = "chicken" in names_lower
        has_eggs = "eggs" in names_lower or "egg" in names_lower
        has_tomato = "tomato" in names_lower or "tomatoes" in names_lower

        steps = []
        # 1. Gather utensils
        steps.append("Set out a cutting board, knife, mixing bowl, pot, pan, spatula, and strainer.")
        # 2–6. Prep each ingredient specifically
        for ing in used:
            steps.append(_prep_step(ing))
        # 7–9. Core cook phases depending on available items
        if has_rice:
            steps.append("Boil 4 cups of water in a pot. Add rinsed rice and simmer on low for 12 minutes.")
            steps.append("Turn off heat, cover, and let rice rest for 5 minutes. Fluff with a fork.")
        if has_chicken:
            steps.append("Heat 1 tbsp oil in a pan over medium. Add chicken and sauté 6–8 minutes until cooked through.")
        if has_eggs:
            steps.append("Grease a pan lightly. Pour in whisked eggs and scramble for 2–3 minutes until softly set.")
        # 10–12. Combine and finish
        combine_bits = []
        if has_rice:
            combine_bits.append("rice")
        if has_chicken:
            combine_bits.append("chicken")
        if has_eggs:
            combine_bits.append("eggs")
        if has_tomato:
            combine_bits.append("diced tomatoes")
        if "chilli" in names_lower or "chili" in names_lower:
            combine_bits.append("sliced chili")
        if combine_bits:
            steps.append(f"In a large bowl, combine {' ,'.join(combine_bits)}. Toss gently with a spatula.")
        steps.append("Season with a pinch of salt and pepper. Taste and adjust seasoning.")
        steps.append("Serve warm. Garnish with chopped herbs if available. Enjoy!")

        # Ensure 10–16 steps; pad with helpful optional tips if short
        while len(steps) < 10:
            steps.append("Clean workspace and organize leftovers in airtight containers for later use.")

        title = _title_from(names_lower, meal_label)
        yt_query = quote_plus(f"{title} easy recipe")
        return {
            "recipe_name": title,
            "ingredients_used": used,
            "steps": steps,
            "prep_time": "10 mins",
            "cook_time": "20 mins",
            "calories": "~400 kcal",
            "youtube_link": f"https://www.youtube.com/results?search_query={yt_query}"
        }

    return {
        "breakfast": _meal("breakfast"),
        "lunch": _meal("lunch"),
        "dinner": _meal("dinner")
    }

def _post_gemini(payload, model: str):
    versions = [DEFAULT_ENDPOINT_VERSION, "v1beta2", "v1"]
    last_error = None
    for ver in versions:
        endpoint = f"https://generativelanguage.googleapis.com/{ver}/models/{model}:generateContent"
        try:
            resp = requests.post(endpoint, params={"key": GEMINI_API_KEY}, json=payload, timeout=30)
            if resp.status_code == 404:
                last_error = Exception(f"404 Not Found for {endpoint}")
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            continue
    if last_error:
        raise last_error

ACTION_VERBS = {
    "peel","wash","rinse","cut","chop","dice","slice","boil","simmer","sauté","saute",
    "mix","whisk","scramble","heat","preheat","drain","strain","season","serve","garnish",
    "toast","stir","fold","marinate","pour","press","cover","rest","reduce","sear"
}

def _step_has_action_verb(s: str) -> bool:
    try:
        first = (s or "").strip().lower().split()[0].strip(".,:;()[]{}")
        return first in ACTION_VERBS
    except Exception:
        return False

def _mentions_unit_or_time(s: str) -> bool:
    t = (s or "").lower()
    units = ["kg","g","cup","cups","tablespoon","tbsp","teaspoon","tsp","ml","l"]
    times = ["minute","minutes","mins","second","seconds","sec"]
    return any(u in t for u in units) or any(tm in t for tm in times)

def _mentions_utensil(s: str) -> bool:
    t = (s or "").lower()
    return any(u in t for u in ["bowl","knife","pot","pan","spatula","strainer","oven","tray","skillet","cutting board"]) 

def _looks_generic(steps: list) -> bool:
    if not steps or len(steps) < 8:
        return True
    generic = 0
    signal = 0
    for s in steps:
        if not _step_has_action_verb(s):
            generic += 1
        if _mentions_unit_or_time(s) or _mentions_utensil(s):
            signal += 1
    return generic > len(steps) // 3 or signal < len(steps) // 3

def _refine_steps_with_gemini(plan: dict) -> dict:
    try:
        original_json = json.dumps(plan, ensure_ascii=False)
        prompt = (
            "You are a cooking instructor. Improve the STEPS ONLY in this meal plan JSON to be granular, action-verb-first, include quantities, utensils, and timing. "
            "Keep recipe_name, ingredients_used, prep_time, cook_time, calories, youtube_link unchanged. Return ONLY JSON, no markdown.\n\n"
            f"Original:\n{original_json}"
        )
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        data = _post_gemini(payload, GEMINI_MODEL)
        candidates = data.get("candidates", [])
        plan_text = None
        for cand in candidates:
            content = cand.get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                if "text" in part:
                    plan_text = part["text"]
                    break
            if plan_text:
                break
        if not plan_text:
            return plan
        text = plan_text.strip()
        if not text.startswith("{"):
            first = text.find("{"); last = text.rfind("}")
            if first != -1 and last != -1 and last > first:
                text = text[first:last+1]
        refined = json.loads(text)
        # Merge only steps back to original to protect other fields
        for key in ["breakfast","lunch","dinner"]:
            if key in plan and key in refined and isinstance(refined[key], dict):
                if isinstance(refined[key].get("steps"), list) and refined[key].get("steps"):
                    plan[key]["steps"] = refined[key]["steps"]
        return plan
    except Exception:
        return plan

def _ensure_step_quality(plan: dict, ingredients: list) -> dict:
    try:
        needs_refine = False
        for key in ["breakfast","lunch","dinner"]:
            if key in plan and isinstance(plan[key], dict):
                steps = plan[key].get("steps") or []
                if _looks_generic(steps):
                    needs_refine = True
        if needs_refine and GEMINI_API_KEY:
            plan = _refine_steps_with_gemini(plan)
        # Final guard: if still generic, borrow detailed steps from local basic generator
        final_needs = False
        for key in ["breakfast","lunch","dinner"]:
            if key in plan and isinstance(plan[key], dict):
                steps = plan[key].get("steps") or []
                if _looks_generic(steps):
                    final_needs = True
        if final_needs:
            local = _basic_meal_plan(ingredients)
            for key in ["breakfast","lunch","dinner"]:
                if key in plan and key in local:
                    plan[key]["steps"] = local[key].get("steps", plan[key].get("steps", []))
        return plan
    except Exception:
        return plan

def generate_meal_plan(ingredients: list):
    """
    Generate a structured meal plan using Gemini.
    ingredients: list of dicts [{"name": "", "quantity": 0, "unit": ""}, ...]
    Returns a dict with breakfast, lunch, dinner
    """
    ingredient_list = "\n".join([f"{i['name']}: {i['quantity']} {i['unit']}" for i in ingredients])

    prompt = f"""
    You are a helpful meal planner.
    Given these ingredients:\n{ingredient_list}
    Generate a healthy one-day meal plan (Breakfast, Lunch, Dinner) using ONLY the available ingredients.
    Minor pantry staples are allowed if necessary (e.g., salt, pepper, oil, basic spices).
    For each recipe, include a relevant YouTube video link demonstrating the recipe.

    STEP WRITING REQUIREMENTS (CRITICAL):
    - Provide 10–16 granular steps per recipe.
    - Each step MUST start with a clear action verb (e.g., peel, wash, chop, boil, sauté, mix, simmer).
    - Include exact quantities and units from `ingredients_used` where relevant in the steps.
    - Include necessary utensils and cookware (e.g., bowl, knife, pot, pan, spatula, strainer) in steps.
    - Include explicit timing where applicable (e.g., "boil for 8 minutes", "simmer for 12 minutes").
    - Keep language beginner-friendly and unambiguous.
    - Use present tense and imperative voice.

    Examples of style:
    - "Peel 1 kg of potatoes. Cut into 1-inch cubes. Rinse and set aside in a bowl."
    - "Wash the chicken and cut into bite-sized pieces."

    Return strictly as JSON with this exact schema (no extra text, no markdown):
    {{
        "breakfast": {{
            "recipe_name": "",
            "ingredients_used": [{{"name": "", "quantity": 0, "unit": ""}}],
            "steps": [],
            "prep_time": "",
            "cook_time": "",
            "calories": "",
            "youtube_link": ""
        }},
        "lunch": {{
            "recipe_name": "",
            "ingredients_used": [{{"name": "", "quantity": 0, "unit": ""}}],
            "steps": [],
            "prep_time": "",
            "cook_time": "",
            "calories": "",
            "youtube_link": ""
        }},
        "dinner": {{
            "recipe_name": "",
            "ingredients_used": [{{"name": "", "quantity": 0, "unit": ""}}],
            "steps": [],
            "prep_time": "",
            "cook_time": "",
            "calories": "",
            "youtube_link": ""
        }}
    }}
    Return ONLY valid JSON and nothing else.
    """
    # Encourage variety across runs with a seed tag
    import random
    variety_seed = str(random.randint(1000, 999999))
    prompt = prompt + f"\nVariety: prefer alternative dish styles; avoid repeating recipe names across runs.\nVarietySeed={variety_seed}\n"

    if not GEMINI_API_KEY:
        print("Gemini not configured. Falling back to dynamic OpenAI generation.")
        try:
            result = openai_generate_meal_plan(ingredients)
            return apply_beginner_mode(result) if BEGINNER_MODE else result
        except Exception:
            result = _ensure_step_quality(_basic_meal_plan(ingredients), ingredients)
            return apply_beginner_mode(result) if BEGINNER_MODE else result

    try:
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": GEMINI_TEMPERATURE,
                "topP": GEMINI_TOP_P,
                "topK": GEMINI_TOP_K
            }
        }
        models_to_try = [GEMINI_MODEL, "gemini-1.5-flash-latest", "gemini-1.5-flash-001"]
        data = None
        for m in models_to_try:
            try:
                data = _post_gemini(payload, m)
                if data:
                    break
            except Exception as e:
                # try next model/version
                data = None
                continue
        if not data:
            raise Exception("Gemini API failed across all fallbacks")

        # Extract text from candidates
        plan_text = None
        try:
            candidates = data.get("candidates", [])
            for cand in candidates:
                content = cand.get("content", {})
                parts = content.get("parts", [])
                for part in parts:
                    if "text" in part:
                        plan_text = part["text"]
                        break
                if plan_text:
                    break
        except Exception:
            plan_text = None

        if not plan_text:
            print("Gemini response had no text. Falling back to dynamic OpenAI generation.")
            try:
                result = openai_generate_meal_plan(ingredients)
                return apply_beginner_mode(result) if BEGINNER_MODE else result
            except Exception:
                result = _ensure_step_quality(_basic_meal_plan(ingredients), ingredients)
                return apply_beginner_mode(result) if BEGINNER_MODE else result

        plan_text_stripped = plan_text.strip()
        if not plan_text_stripped.startswith("{"):
            first = plan_text_stripped.find("{")
            last = plan_text_stripped.rfind("}")
            if first != -1 and last != -1 and last > first:
                plan_text_stripped = plan_text_stripped[first:last+1]

        plan_json = json.loads(plan_text_stripped)
        plan_json = _ensure_step_quality(plan_json, ingredients)
        if BEGINNER_MODE:
            plan_json = apply_beginner_mode(plan_json)
        return plan_json
    except Exception as e:
        print("Gemini generation error:", e)
        try:
            result = openai_generate_meal_plan(ingredients)
            return apply_beginner_mode(result) if BEGINNER_MODE else result
        except Exception:
            result = _ensure_step_quality(_basic_meal_plan(ingredients), ingredients)
            return apply_beginner_mode(result) if BEGINNER_MODE else result