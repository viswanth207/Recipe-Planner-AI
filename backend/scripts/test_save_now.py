import requests
import os
from dotenv import load_dotenv

# Load env (front and back)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Read token generated earlier (or regenerate if needed)
TOKEN = os.getenv('TEST_JWT_TOKEN', '')
if not TOKEN:
    # Fallback: try reading token printed earlier from file if exists
    token_path = os.path.join(os.path.dirname(__file__), '..', 'token.txt')
    if os.path.exists(token_path):
        with open(token_path, 'r') as f:
            TOKEN = f.read().strip()

if not TOKEN:
    # Hardcode from prior run if necessary; replace as needed
    TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzYWlAZ21haWwuY29tIiwiZXhwIjoxNzYwODU5OTgzfQ.C6m4vy5WxuTns7jfba1r8SYxpUMGYidP0bcRPBazWKg'

url = 'http://127.0.0.1:8000/mealplan/save-now'
headers = {'Authorization': f'Bearer {TOKEN}'}

r = requests.post(url, headers=headers)
print('status:', r.status_code)
print('json:', r.json())