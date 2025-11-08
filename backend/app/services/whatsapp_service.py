import requests
import os
from dotenv import load_dotenv
from app.config import WHATSAPP_TEMPLATE_HELLO, WHATSAPP_TEMPLATE_LANG


# Sanitization helpers to improve recipe readability
def _normalize_ingredients(ingredients):
    normalized = []
    for ing in (ingredients or []):
        name = str(ing.get('name', '')).strip()
        qty = ing.get('quantity')
        unit = ing.get('unit')
        # Convert dozens to pieces for clarity
        if isinstance(unit, str) and unit.lower() == 'dozen' and isinstance(qty, (int, float)):
            qty = float(qty) * 12
            unit = 'pieces'
        normalized.append({'name': name or 'Unknown', 'quantity': qty, 'unit': unit})
    return normalized


def _sanitize_steps(steps, ingredients):
    if not steps:
        return []
    lower_names = [(ing.get('name') or '').lower() for ing in (ingredients or [])]
    packaged = set(['biscuits', 'cornflakes', 'bread', 'maggi', 'papad', 'tomato ketchup', 'peanut butter', 'tea', 'coffee', 'sugar'])
    dals = set(['chana dal', 'toor dal', 'moong dal', 'masoor dal', 'rajma'])

    equipment_terms = ['cutting board', 'knife', 'mixing bowl', 'pot', 'pan', 'spatula', 'strainer', 'colander']

    def fix_line(line):
        s = str(line).strip()
        ls = s.lower()
        # Remove only when the line is an equipment list or workspace setup
        eq_count = sum(1 for term in equipment_terms if term in ls)
        if ls.startswith('set out') or 'prepare your workspace' in ls or eq_count >= 3:
            return ''
        # Specific corrections
        if 'wash and chop chana dal' in ls:
            return 'Rinse chana dal; boil until tender; season to taste.'
        if 'wash and chop cornflakes' in ls:
            return 'Cornflakes are ready-to-eat; sprinkle on top for crunch.'
        if 'wash and chop bread' in ls:
            return 'Toast bread and cut into pieces.'
        # Generic corrections based on ingredient category
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
    # Deduplicate while preserving order, cap to 10 steps
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


class WhatsAppService:
    def __init__(self):
        load_dotenv()
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_phone = os.getenv('TWILIO_PHONE_NUMBER')
        self.base_url = f'https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json'

    def _normalize_whatsapp_number(self, number: str) -> str:
        """
        Normalize a phone number to Twilio WhatsApp format: 'whatsapp:+<E.164>'
        Accepts inputs like '+<digits>', 'whatsapp:+<digits>', or '<digits>'.
        """
        if not number:
            return number
        number = number.strip()
        # If already in Twilio WhatsApp format
        if number.lower().startswith('whatsapp:'):
            # Ensure '+' after prefix
            suffix = number.split(':', 1)[1]
            if not suffix.startswith('+'):
                suffix = '+' + suffix
            return f'whatsapp:{suffix}'
        # Ensure leading '+' for E.164
        if not number.startswith('+'):
            number = '+' + number
        return f'whatsapp:{number}'

    def send_message(self, to_phone, message):
        # Guard missing credentials
        if not self.account_sid or not self.auth_token:
            return {'status': 'error', 'message': 'Twilio credentials missing (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN).'}
        if not self.from_phone:
            return {'status': 'error', 'message': 'Twilio WhatsApp sender missing (TWILIO_PHONE_NUMBER).'}

        from_whatsapp = self._normalize_whatsapp_number(self.from_phone or '')
        to_whatsapp = self._normalize_whatsapp_number(to_phone or '')

        payload = {
            'From': from_whatsapp,
            'To': to_whatsapp,
            'Body': message,
        }
        
        headers = {'Accept': 'application/json'}
        auth = (self.account_sid, self.auth_token)

        try:
            response = requests.post(self.base_url, data=payload, headers=headers, auth=auth, timeout=20)
            if response.status_code == 201:
                print(f'WhatsApp message sent successfully to {to_phone}')
                return {
                    'status': 'success',
                    'message': 'Message sent successfully',
                    'response': response.json(),
                    'normalized_from': from_whatsapp,
                    'normalized_to': to_whatsapp,
                }
            else:
                text = response.text
                print(f'Failed to send WhatsApp message: {response.status_code} - {text}')
                # Heuristic hints for common Twilio sandbox issues
                hint = None
                lower = text.lower()
                if 'sandbox' in lower or 'participant' in lower or 'not joined' in lower:
                    hint = 'Recipient likely not joined Twilio WhatsApp sandbox.'
                elif 'sender' in lower and 'not' in lower and 'approved' in lower:
                    hint = 'Twilio WhatsApp sender not approved or incorrect.'
                elif 'invalid' in lower and 'from' in lower:
                    hint = 'Invalid From number; check TWILIO_PHONE_NUMBER.'
                return {
                    'status': 'error',
                    'message': f'Failed to send message: {response.status_code}',
                    'response': text,
                    'payload': payload,
                    'normalized_from': from_whatsapp,
                    'normalized_to': to_whatsapp,
                    'twilio_hint': hint,
                }
        except Exception as e:
            print(f'Error sending WhatsApp message: {str(e)}')
            return {'status': 'error', 'message': f'Exception occurred: {str(e)}'}

    def format_meal_plan_message(self, meal_plan):
        """
        Format message for WhatsApp given a plan shaped like:
        {"breakfast": {...}, "lunch": {...}, "dinner": {...}} or a subset.
        Also supports legacy {"meals": [...], "user_name": "..."} payloads.
        """
        user_name = meal_plan.get("user_name", "there")
        message = f'Hey {user_name}!\nHere is your recipe plan for today\n\n'

        # Prefer new schema keys
        keys = [k for k in ["breakfast", "lunch", "dinner"] if isinstance(meal_plan.get(k), dict) and meal_plan.get(k)]
        if keys:
            for key in keys:
                recipe = meal_plan.get(key, {})
                recipe = _sanitize_recipe(recipe)
                recipe_name = recipe.get('recipe_name') or recipe.get('name') or key.title()
                message += f'*{key.title()}*: {recipe_name}\n'

                ingredients = recipe.get('ingredients_used') or recipe.get('ingredients') or []
                for ing in ingredients:
                    name = ing.get('name', 'Unknown')
                    qty = ing.get('quantity')
                    unit = ing.get('unit')
                    if qty and unit:
                        message += f'- {name}: {qty} {unit}\n'
                    elif qty:
                        message += f'- {name}: {qty}\n'
                    else:
                        message += f'- {name}\n'

                steps = recipe.get('steps') or []
                if steps:
                    message += '\nSteps:\n'
                    for i, step in enumerate(steps, 1):
                        message += f'{i}. {step}\n'
                if recipe.get('youtube_link'):
                    message += f'\nVideo: {recipe.get("youtube_link")}\n'
                message += '\n'
        else:
            # Legacy schema support
            for meal in meal_plan.get('meals', []):
                meal_type = meal.get('type', 'Meal')
                recipe = meal.get('recipe', {})
                recipe = _sanitize_recipe(recipe)
                recipe_name = recipe.get('name', 'Recipe')
                message += f'*{meal_type}*: {recipe_name}\n'
                ingredients = recipe.get('ingredients_used') or recipe.get('ingredients') or []
                for ingredient in ingredients:
                    ingredient_name = ingredient.get('name', 'Unknown')
                    quantity = ingredient.get('quantity', 1)
                    unit = ingredient.get('unit')
                    if unit:
                        message += f'- {ingredient_name}: {quantity} {unit}\n'
                    else:
                        message += f'- {ingredient_name}: {quantity}\n'
                steps = recipe.get('steps', [])
                if steps:
                    message += '\nSteps:\n'
                    for i, step in enumerate(steps, 1):
                        message += f'{i}. {step}\n'
                message += '\n'

        message += 'Happy cooking!'
        return message


# Helper functions for backwards compatibility
def send_mealplan_whatsapp(user_phone: str, meal_plan: dict, user_name: str = "User"):
    """Send a meal plan via WhatsApp"""
    whatsapp_service = WhatsAppService()
    # Support new schema by merging the plan with user_name
    payload = {'user_name': user_name}
    if isinstance(meal_plan, dict):
        payload.update(meal_plan)
    message_text = whatsapp_service.format_meal_plan_message(payload)
    result = whatsapp_service.send_message(user_phone, message_text)
    
    # Return format expected by scheduler.py
    msg_id = None
    status = None
    if result.get('status') == 'success':
        msg_id = result.get('response', {}).get('sid')
        status = 'accepted'
    
    return (msg_id, status, result)


def send_template_whatsapp(user_phone: str, template_name: str = "hello_world", language_code: str = "en_US"):
    """Send a template message via WhatsApp
    Behavior:
    - If an approved template body is set via env (WHATSAPP_TEMPLATE_HELLO), use it and substitute a basic placeholder.
    - Otherwise, send a minimal hello message. Note: In Twilio Sandbox, recipients must still join.
    """
    whatsapp_service = WhatsAppService()
    # Prefer configured approved template body; Twilio will route as template if it matches.
    lang = (language_code or WHATSAPP_TEMPLATE_LANG or "en_US")
    body = (WHATSAPP_TEMPLATE_HELLO or '').strip()
    if body:
        # Replace first placeholder {{1}} with a generic string to start conversation.
        # Additional placeholders can be filled if present.
        msg = body.replace("{{1}}", "friend").replace("{{ 1 }}", "friend")
        template_message = msg
    else:
        # Fallback simple message (may be blocked by WhatsApp for first contact on production senders)
        template_message = f"Hello! Your daily recipe plan is ready. ({template_name} / {lang})"

    result = whatsapp_service.send_message(user_phone, template_message)
    
    # Return format expected by routes
    msg_id = None
    status = None
    if result.get('status') == 'success':
        msg_id = result.get('response', {}).get('sid')
        status = 'accepted'

    return (msg_id, status, result)


def process_whatsapp_reply(from_number: str, message_body: str):
    """Process incoming WhatsApp replies"""
    print(f"Processing WhatsApp reply from {from_number}: {message_body}")
    # Basic implementation - just log for now
    # Add more sophisticated processing later if needed
    return
