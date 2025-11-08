"""
Voicebot FastAPI server for restaurant reservations (MongoDB backend)
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import logging
from dotenv import load_dotenv

from jwt_auth import JWTManager, get_current_user_from_token, get_current_user_optional
from gemini_service import gemini_service

load_dotenv()

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "restaurant_reservation_db"

app = FastAPI(title="Restaurant Voicebot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mongo_client = None
database = None

def get_database():
    global mongo_client, database
    if mongo_client is None:
        mongo_client = MongoClient(MONGODB_URL)
        database = mongo_client[DATABASE_NAME]
    return database

def convert_objectid(doc: Dict[str, Any]):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
        doc["id"] = doc["_id"]
    return doc

@app.get("/")
async def root():
    return {"message": "Restaurant Voicebot API", "database": "MongoDB"}

@app.get("/voicebot/status")
async def get_voicebot_status():
    return {
        "gemini_enabled": gemini_service.is_enabled(),
        "features": {
            "intelligent_processing": gemini_service.is_enabled(),
            "restaurant_matching": True,
            "reservation_booking": True,
            "conversation": gemini_service.is_enabled(),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.post("/voicebot/process")
async def process_voice_command(
    command_data: dict, 
    current_user: dict = Depends(get_current_user_optional)
):
    try:
        command = command_data.get("command", "").strip()
        user_context = command_data.get("context", {})
        if not command:
            raise HTTPException(status_code=400, detail="Command is required")

        db = get_database()
        restaurants_collection = db["restaurants"]
        restaurants_cursor = restaurants_collection.find(
            {"is_active": True}, {"name": 1, "city": 1, "state": 1, "cuisine": 1}
        ).sort("name", 1)

        restaurant_list = []
        for r in restaurants_cursor:
            restaurant_list.append({
                "id": str(r["_id"]),
                "name": r.get("name", "Unknown"),
                "city": r.get("city", "Unknown"),
                "state": r.get("state", "Unknown"),
                "cuisine": r.get("cuisine", "Unknown"),
            })

        if current_user:
            user_context.update({
                "user_email": current_user.get("email"),
                "user_id": current_user.get("user_id"),
            })

        result = await gemini_service.process_voice_command(
            command, restaurant_list, user_context
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing voice command: {e}")
        raise HTTPException(status_code=500, detail="Failed to process voice command")

@app.post("/restaurants/debug/seed")
async def seed_sample_restaurants():
    try:
        db = get_database()
        collection = db["restaurants"]
        existing_count = collection.count_documents({})
        if existing_count > 0:
            return {"message": "Restaurants already exist", "count": existing_count}
        sample_restaurants = [
            {"name": "Pizza World", "city": "Bangalore", "state": "Karnataka", "cuisine": "Italian", "is_active": True},
            {"name": "Hotel TAJ", "city": "Bangalore", "state": "Karnataka", "cuisine": "Indian", "is_active": True},
            {"name": "Hotel Vivana", "city": "Bangalore", "state": "Karnataka", "cuisine": "Multi-Cuisine", "is_active": True},
            {"name": "Hotel Nagasai", "city": "Bangalore", "state": "Karnataka", "cuisine": "South Indian", "is_active": True},
        ]
        result = collection.insert_many(sample_restaurants)
        return {"inserted": len(result.inserted_ids)}
    except Exception as e:
        logger.error(f"Error seeding sample restaurants: {e}")
        raise HTTPException(status_code=500, detail="Failed to seed restaurants")

@app.get("/restaurants/debug/all-names")
async def get_all_restaurant_names():
    try:
        db = get_database()
        collection = db["restaurants"]
        restaurants = list(collection.find({"is_active": True}, {"name": 1, "city": 1, "state": 1}))
        data = []
        for r in restaurants:
            data.append({"id": str(r["_id"]), "name": r.get("name", "Unknown"), "city": r.get("city", "Unknown"), "state": r.get("state", "Unknown")})
        return {"total_count": len(data), "restaurants": data}
    except Exception as e:
        logger.error(f"Error fetching all restaurant names: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch restaurant names")

if __name__ == "__main__":
    import uvicorn
    print("Starting MongoDB FastAPI Server...")
    print("Server running at: http://localhost:8001")
    print("API Documentation: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)