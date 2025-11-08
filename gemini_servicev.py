import os
from typing import List, Dict, Any, Optional


class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    async def process_voice_command(
        self,
        command: str,
        restaurants: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        text = command.lower()

        intent = "other"
        if any(k in text for k in ["book", "reserve", "reservation", "table"]):
            intent = "reservation"

        matched: Optional[Dict[str, Any]] = None
        for r in restaurants:
            if r.get("name") and r["name"].lower() in text:
                matched = {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "city": r.get("city"),
                    "state": r.get("state"),
                    "cuisine": r.get("cuisine"),
                    "confidence": 0.7,
                }
                break

        response_message = (
            "I understood your request. Let me help you with that."
            if intent == "reservation"
            else "How can I assist you today?"
        )

        return {
            "intent": intent,
            "confidence": 0.6,
            "restaurant_match": matched,
            "response_message": response_message,
            "action_required": "book_table" if matched and intent == "reservation" else "provide_info",
        }

    async def generate_conversation_response(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "message": "How can I assist further?",
            "context": context or {},
        }