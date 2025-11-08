import os
from typing import Dict, List

BEGINNER_MODE = os.getenv("BEGINNER_MODE", "true").lower() == "true"

TOOLS_LINE = (
    "Set out tools: sieve/strainer, bowl, measuring cup, pot with lid,"
    " pan/toaster, spatula, knife, and cutting board."
)


def _find_ing(ingredients: List[Dict], names: List[str]):
    names_l = {n.lower() for n in names}
    for ing in ingredients or []:
        name = (ing.get("name") or "").lower().strip()
        if name in names_l:
            return ing
    return None


def _format_qty(ing: Dict, default_qty: str = "") -> str:
    if not ing:
        return default_qty
    q = ing.get("quantity")
    u = ing.get("unit") or ""
    if q is None or q == "":
        return default_qty or u
    try:
        qf = float(q)
        # avoid trailing .0 for ints
        if qf.is_integer():
            q_str = str(int(qf))
        else:
            q_str = str(qf)
    except Exception:
        q_str = str(q)
    return f"{q_str} {u}".strip()


def _build_dal_steps(ingredients: List[Dict]) -> List[str]:
    dal = _find_ing(ingredients, ["chana dal", "dal", "lentils"])
    if not dal:
        return []
    dal_qty = _format_qty(dal, "200 g")
    steps = [
        TOOLS_LINE,
        f"Measure {dal_qty} chana dal using a measuring cup.",
        "Pick out any stones or debris.",
        "Rinse dal in a sieve under running water for 60 seconds.",
        "Optional: soak dal in 3 cups water for 30–60 minutes; drain.",
        "Add dal to a pot with 3 cups fresh water.",
        "Set heat to high; bring to a steady boil (5–7 minutes). Skim foam.",
        "Reduce heat to low–medium; partially cover with lid.",
        "Simmer 25–35 minutes; stir every 5–7 minutes.",
        "Add ½ teaspoon salt and ¼ teaspoon turmeric (optional). Stir.",
        "Check doneness: press a dal grain; it should be soft, not chalky.",
        "If firm, add ½ cup water and cook 5–10 minutes more.",
        "Adjust consistency with 2–3 tablespoons hot water; taste and season.",
    ]
    return steps


def _build_bread_steps(ingredients: List[Dict]) -> List[str]:
    bread = _find_ing(ingredients, ["bread", "bread slices"])
    if not bread:
        return []
    slices = _format_qty(bread, "4 slices")
    return [
        "Preheat a pan to medium or use a toaster.",
        f"Toast {slices} until golden (1–2 minutes per side).",
        "Optional: add a teaspoon butter or oil for flavor.",
        "Rest toast 30 seconds; cut into triangles with a knife.",
    ]


def _build_apple_steps(ingredients: List[Dict]) -> List[str]:
    apples = _find_ing(ingredients, ["apple", "apples"])
    if not apples:
        return []
    qty = _format_qty(apples, "2 pieces")
    return [
        f"Wash {qty} apples under running water.",
        "Core apples with a knife; discard seeds.",
        "Slice into thin wedges on a cutting board.",
        "Optional: drizzle a few drops of lemon juice to prevent browning.",
    ]


def _build_banana_steps(ingredients: List[Dict]) -> List[str]:
    bananas = _find_ing(ingredients, ["banana", "bananas"])
    if not bananas:
        return []
    qty = _format_qty(bananas, "2 pieces")
    return [
        f"Peel {qty} bananas.",
        "Slice into bite-size rounds; set aside in a bowl.",
    ]


def _build_cornflakes_steps(ingredients: List[Dict]) -> List[str]:
    cornflakes = _find_ing(ingredients, ["cornflakes"])
    if not cornflakes:
        return []
    qty = _format_qty(cornflakes, "200 g")
    return [
        "Place a clean serving bowl on the counter.",
        f"Add {qty} cornflakes to the bowl.",
        "Top with prepared fruit (apple wedges, banana slices).",
        "Optional: drizzle 1 teaspoon honey; serve immediately.",
    ]


def _pad_to_range(steps: List[str], min_len: int = 12, max_len: int = 16) -> List[str]:
    extras = [
        "Taste and adjust salt and pepper.",
        "Garnish with chopped herbs if available.",
        "Clean workspace and wash utensils.",
        "Store leftovers in airtight containers after cooling.",
    ]
    i = 0
    while len(steps) < min_len and i < len(extras):
        steps.append(extras[i])
        i += 1
    # Cap
    return steps[:max_len]


def _build_beginner_steps(recipe: Dict) -> List[str]:
    ing = recipe.get("ingredients_used") or []
    steps: List[str] = []

    # Prioritize main-cook flows first (dal), then sides and assembly
    dal_steps = _build_dal_steps(ing)
    if dal_steps:
        steps.extend(dal_steps)

    bread_steps = _build_bread_steps(ing)
    if bread_steps:
        steps.extend(bread_steps)

    apple_steps = _build_apple_steps(ing)
    if apple_steps:
        steps.extend(apple_steps)

    banana_steps = _build_banana_steps(ing)
    if banana_steps:
        steps.extend(banana_steps)

    cornflakes_steps = _build_cornflakes_steps(ing)
    if cornflakes_steps:
        steps.extend(cornflakes_steps)

    if not steps:
        # If nothing matched, keep original but prepend tools and basic clarifications
        original = recipe.get("steps") or []
        steps = [TOOLS_LINE]
        steps.extend(original)

    steps = _pad_to_range(steps)
    return steps


def apply_beginner_mode(plan: Dict) -> Dict:
    try:
        for key in ["breakfast", "lunch", "dinner"]:
            if key in plan and isinstance(plan[key], dict):
                plan[key]["steps"] = _build_beginner_steps(plan[key])
        return plan
    except Exception:
        return plan