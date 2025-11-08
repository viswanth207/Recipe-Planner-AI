from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.routes import auth_routes, ingredient_routes, mealplan_routes, whatsapp_routes
from app.services.scheduler import start_scheduler
from app.database import init_indexes
from app.routes import agentic_routes

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS to allow frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])  # auth has no internal prefix
app.include_router(ingredient_routes.router)  # router already has "/ingredients" prefix
app.include_router(mealplan_routes.router)    # router already has "/mealplan" prefix
app.include_router(whatsapp_routes.router)    # router already has "/whatsapp" prefix
app.include_router(agentic_routes.router)     # new orchestration endpoints

@app.on_event("startup")
def _startup():
    try:
        init_indexes()
        logger.info("MongoDB indexes ensured")
    except Exception as e:
        logger.warning(f"Index initialization failed: {e}")
    try:
        start_scheduler()
        logger.info("Scheduler started")
    except Exception as e:
        # Avoid crashing app if scheduler fails
        logger.warning(f"Failed to start scheduler: {e}")
