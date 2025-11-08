from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models import Ingredient
from app.database import ingredients_col
from bson import ObjectId
from app.auth import decode_access_token

router = APIRouter(prefix="/ingredients", tags=["ingredients"])

def get_user_id(user_id: str = Depends(decode_access_token)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id

@router.post("/")
def add_ingredient(ingredient: Ingredient, user_id: str = Depends(decode_access_token)):
    data = ingredient.dict()
    data["user_id"] = user_id
    ingredients_col.insert_one(data)
    return {"message": "Ingredient added"}

@router.get("/", response_model=List[Ingredient])
def list_ingredients(user_id: str = Depends(decode_access_token)):
    items = list(ingredients_col.find({"user_id": user_id}, {"_id": 0}))
    return items

@router.put("/{ingredient_name}")
def update_ingredient(ingredient_name: str, ingredient: Ingredient, user_id: str = Depends(decode_access_token)):
    result = ingredients_col.update_one(
        {"user_id": user_id, "name": ingredient_name},
        {"$set": ingredient.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return {"message": "Ingredient updated"}

@router.delete("/{ingredient_name}")
def delete_ingredient(ingredient_name: str, user_id: str = Depends(decode_access_token)):
    result = ingredients_col.delete_one({"user_id": user_id, "name": ingredient_name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return {"message": "Ingredient deleted"}
