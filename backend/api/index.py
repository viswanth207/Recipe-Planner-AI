import os
import sys

# Ensure Python can import from both `backend/` and repository root
_current_dir = os.path.dirname(__file__)
_project_root = os.path.abspath(os.path.join(_current_dir, ".."))
_repo_root = os.path.abspath(os.path.join(_project_root, ".."))
for _p in (_project_root, _repo_root):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from app.main import app
except Exception as e:
    try:
        from backend.app.main import app  # type: ignore
    except Exception:
        import traceback
        print("[Vercel] Failed to import FastAPI app:", e, file=sys.stderr)
        traceback.print_exc()
        raise

# Vercel’s Python serverless runtime auto-detects `app` as ASGI application.