try:
    # When Vercel project root is set to `backend/`, import from `app` directly
    from app.main import app
except Exception as e:
    # Fallback for repository-root deployments where `backend` is the package
    try:
        from backend.app.main import app  # type: ignore
    except Exception:
        import sys, traceback
        print("[Vercel] Failed to import FastAPI app:", e, file=sys.stderr)
        traceback.print_exc()
        raise

# Vercel’s Python serverless runtime auto-detects `app` as ASGI application.