import os
import json
import random
import string
import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

def rand_email(prefix="qa.user"):
    suffix = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    return f"{prefix}.{suffix}@example.com"


def main():
    email = rand_email()
    password = "Test123!"
    phone = "+14155550000"

    signup_payload = {
        "name": "QA User",
        "email": email,
        "phone": phone,
        "password": password,
    }

    r = requests.post(f"{BASE_URL}/auth/signup", json=signup_payload, timeout=10)
    print("Signup status:", r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)

    login_payload = {"email": email, "password": password, "phone": phone}
    r2 = requests.post(f"{BASE_URL}/auth/login", json=login_payload, timeout=10)
    print("Login status:", r2.status_code)
    try:
        print(json.dumps(r2.json(), indent=2))
    except Exception:
        print(r2.text)

    # Attempt /auth/me with token
    if r2.status_code == 200 and "access_token" in r2.json():
        token = r2.json()["access_token"]
        r3 = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        print("/auth/me status:", r3.status_code)
        try:
            print(json.dumps(r3.json(), indent=2))
        except Exception:
            print(r3.text)

if __name__ == "__main__":
    main()