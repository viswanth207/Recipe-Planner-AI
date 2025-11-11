import os
import sys

# Ensure we can import the FastAPI app from backend
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
BACKEND_ROOT = os.path.join(REPO_ROOT, "backend")
for p in [BACKEND_ROOT, REPO_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    # Preferred import path when backend is a package
    from backend.app.main import app  # type: ignore
except Exception:
    # Fallback if repository layout differs
    from app.main import app  # type: ignore

# Vercel auto-detects the ASGI application named `app`.