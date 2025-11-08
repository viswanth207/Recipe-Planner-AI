"""
Gemini AI Service for Restaurant Voicebot
Provides intelligent conversation and command processing capabilities
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        """Initialize Gemini AI service"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("Gemini API key not found or not set. AI features will be limited.")
            self.enabled = False
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.enabled = True
            logger.info("Gemini AI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {e}")
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if Gemini service is enabled"""
        return self.enabled
    
    async def process_voice_command(self, 
                                  command: str, 
                                  available_restaurants: List[Dict], 
                                  user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process voice command using Gemini AI for intelligent interpretation
        
        Args:
            command: User's voice command
            available_restaurants: List of available restaurants
            user_context: Optional user context (location, preferences, etc.)
        
        Returns:
            Dict with processed command information
        """
        if not self.enabled:
            return self._fallback_processing(command, available_restaurants)
        
        try:
            # Prepare restaurant context for AI - use ALL restaurants
            restaurant_names = [r.get('name', '') for r in available_restaurants]  # No limit - use all restaurants
            
            # Debug: Log the restaurants being sent to AI
            logger.info(f"Restaurant names being sent to AI: {restaurant_names}")
            
            # Create detailed prompt for restaurant reservation processing
            prompt = self._create_reservation_prompt(command, restaurant_names, user_context)
            
            # Generate response from Gemini
            response = self.model.generate_content(prompt)
            
            # Debug: Log the raw AI response
            logger.info(f"Raw AI response: {response.text}")
            
            # Parse the AI response
            result = self._parse_ai_response(response.text, available_restaurants)
            logger.info(f"Parsed AI response: {result}")
            
            # Fallback: If AI didn't find restaurant but we can match it manually
            if not result.get("restaurant_match", {}).get("found", False) and result.get("intent") == "reservation":
                manual_match = self._manual_restaurant_search(command, available_restaurants)
                if manual_match.get("found"):
                    logger.info(f"Manual fallback found restaurant: {manual_match['name']}")
                    result["restaurant_match"] = manual_match
                    result["response_message"] = f"Great! I found {manual_match['name']}. Let me help you make a reservation."
                    result["action_required"] = "book_table"
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing command with Gemini: {e}")
            return self._fallback_processing(command, available_restaurants)
    
    def _create_reservation_prompt(self, 
                                 command: str, 
                                 restaurant_names: List[str], 
                                 user_context: Optional[Dict] = None) -> str:
        """Create a detailed prompt for restaurant reservation processing"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        prompt = f"""
You are an intelligent restaurant reservation assistant. Process the user's voice command and extract reservation details.

**USER COMMAND:** "{command}"

**AVAILABLE RESTAURANTS:** {', '.join(restaurant_names)}

**CURRENT DATE/TIME:** {current_time}
**CURRENT MONTH:** October 2025 (when user says numeric dates like "25", assume current month unless impossible)

**TASK:** Analyze the command and return a JSON response with the following structure:

{{
    "intent": "reservation|greeting|question|help|other",
    "confidence": 0.0-1.0,
    "restaurant_match": {{
        "found": true/false,
        "name": "exact restaurant name from the list",
        "confidence": 0.0-1.0,
        "alternatives": ["alternative1", "alternative2"]
    }},
    "reservation_details": {{
        "guests": number,
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "special_requests": "any special requirements"
    }},
    "response_message": "helpful response to the user",
    "action_required": "book_table|show_restaurants|ask_clarification|provide_info"
}}

**GUIDELINES:**
1. **RESTAURANT MATCHING IS FLEXIBLE**: Match names case-insensitively and with partial matches
   - "pizza world" matches "Pizza World" or "pizza world" 
   - "central plaza" can match restaurants with "Plaza" or "Central" in the name
   - Always check the EXACT list provided - if a name appears in the list, it's a valid match
2. Extract number of guests from various formats:
   - Numbers: "4 people", "6 guests", "party of 8"
   - Words: "two people", "four of us", "six guests"
   - Mixed: "for 2", "table for four", "party of 3"
3. Parse time expressions like "7 PM", "eight thirty", "evening", "lunch time"
4. Parse date expressions in multiple formats:
   - Relative: "today", "tomorrow", "next Friday", "this weekend"
   - Numeric: "25", "13th", "1st", "on 5", "the 20th"
   - Assume current month/year if only day number given
   - Convert to YYYY-MM-DD format
5. Default values: guests=2, time="19:00", date=today
6. Be conversational and helpful in response_message
7. **IMPORTANT**: If you find ANY restaurant name in the list that matches (even partially), set "found": true
8. Return ONLY valid JSON, no extra text

**EXAMPLES:**
- "Book a table at TAJ for 4 people at 7 PM" -> find "Hotel TAJ", guests=4, time="19:00"
- "Reserve nagasai for two tomorrow" -> find "Hotel Nagasai", guests=2, date=tomorrow
- "Table for 6 at vivana this evening" -> find "Hotel Vivana", guests=6, time="19:00"
- "Book Pizza world for 4" -> if "pizza world" is in the list, set found=true, name="pizza world"
- "Book table for 4 on 25" -> guests=4, date="2025-10-25" (assume current month)
- "Reserve for 2 on the 13th" -> guests=2, date="2025-10-13"
- "Table for 4 on 1st" -> guests=4, date="2025-10-01"
"""
        
        return prompt
    
    def _parse_ai_response(self, ai_response: str, available_restaurants: List[Dict]) -> Dict[str, Any]:
        """Parse AI response and validate against available data"""
        try:
            # Clean the response - sometimes AI adds extra text
            response_text = ai_response.strip()
            
            # Find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_text = response_text[json_start:json_end]
            parsed_response = json.loads(json_text)
            
            # Validate and enhance the response
            return self._validate_ai_response(parsed_response, available_restaurants)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI response: {e}, Response: {ai_response}")
            return {
                "intent": "reservation",
                "confidence": 0.5,
                "restaurant_match": {"found": False, "name": "", "confidence": 0.0},
                "response_message": "I had trouble understanding your request. Please try again.",
                "action_required": "ask_clarification"
            }
    
    def _validate_ai_response(self, response: Dict, available_restaurants: List[Dict]) -> Dict[str, Any]:
        """Validate and enhance AI response with actual restaurant data"""
        
        # Validate restaurant match
        if response.get("restaurant_match", {}).get("found", False):
            suggested_name = response["restaurant_match"].get("name", "")
            
            # Find exact match in available restaurants
            matched_restaurant = None
            for restaurant in available_restaurants:
                if restaurant.get("name", "").lower() == suggested_name.lower():
                    matched_restaurant = restaurant
                    break
            
            if matched_restaurant:
                response["restaurant_match"]["restaurant_id"] = matched_restaurant.get("id")
                response["restaurant_match"]["restaurant_data"] = matched_restaurant
            else:
                # Try fuzzy matching
                response["restaurant_match"] = self._find_best_restaurant_match(
                    suggested_name, available_restaurants
                )
        
        # Validate reservation details
        if "reservation_details" in response:
            details = response["reservation_details"]
            
            # Validate date format
            if "date" in details:
                try:
                    datetime.strptime(details["date"], "%Y-%m-%d")
                except ValueError:
                    details["date"] = datetime.now().strftime("%Y-%m-%d")
            
            # Validate time format
            if "time" in details:
                try:
                    datetime.strptime(details["time"], "%H:%M")
                except ValueError:
                    details["time"] = "19:00"
            
            # Validate guests
            if "guests" in details and not isinstance(details["guests"], int):
                details["guests"] = 2
        
        return response
    
    def _manual_restaurant_search(self, command: str, restaurants: List[Dict]) -> Dict[str, Any]:
        """Manual restaurant search as fallback when AI fails"""
        command_lower = command.lower()
        
        # Extract potential restaurant names from the command
        # Look for common patterns: "at [restaurant]", "book [restaurant]", etc.
        import re
        patterns = [
            r'at\s+([^,\s](?:[^,]*[^,\s])?)',  # "at Pizza World"
            r'book\s+([^,\s](?:[^,]*[^,\s])?)',  # "book Pizza World"
            r'reserve\s+([^,\s](?:[^,]*[^,\s])?)',  # "reserve Pizza World"
        ]
        
        potential_names = []
        for pattern in patterns:
            matches = re.findall(pattern, command_lower)
            potential_names.extend(matches)
        
        # Also try splitting and looking for multi-word restaurant names
        words = command_lower.split()
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):  # Check up to 3-word names
                potential_name = ' '.join(words[i:j])
                if len(potential_name) > 3:  # Avoid very short matches
                    potential_names.append(potential_name)
        
        # Search for matches
        for potential_name in potential_names:
            match = self._find_best_restaurant_match(potential_name.strip(), restaurants)
            if match.get("found"):
                return match
        
        return {"found": False, "name": "", "confidence": 0.0}

    def _find_best_restaurant_match(self, search_name: str, restaurants: List[Dict]) -> Dict[str, Any]:
        """Find best restaurant match using fuzzy logic"""
        if not search_name:
            return {"found": False, "name": "", "confidence": 0.0}
        
        search_lower = search_name.lower().strip()
        best_match = None
        best_confidence = 0.0
        alternatives = []
        
        for restaurant in restaurants:
            name = restaurant.get("name", "").lower()
            
            # Exact match
            if name == search_lower:
                return {
                    "found": True,
                    "name": restaurant.get("name"),
                    "confidence": 1.0,
                    "restaurant_id": restaurant.get("id"),
                    "restaurant_data": restaurant
                }
            
            # Partial matches
            confidence = 0.0
            if search_lower in name or name in search_lower:
                confidence = 0.8
            elif any(word in name for word in search_lower.split() if len(word) > 2):
                confidence = 0.6
            elif any(word in search_lower for word in name.split() if len(word) > 2):
                confidence = 0.6
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = restaurant
            
            if confidence > 0.5:
                alternatives.append(restaurant.get("name"))
        
        if best_match and best_confidence > 0.6:
            return {
                "found": True,
                "name": best_match.get("name"),
                "confidence": best_confidence,
                "restaurant_id": best_match.get("id"),
                "restaurant_data": best_match,
                "alternatives": alternatives[:3]
            }
        else:
            return {
                "found": False,
                "name": search_name,
                "confidence": 0.0,
                "alternatives": alternatives[:5]
            }
    
    def _fallback_processing(self, command: str, available_restaurants: List[Dict]) -> Dict[str, Any]:
        """Fallback processing when Gemini is not available"""
        command_lower = command.lower()
        
        # Simple intent detection
        if any(word in command_lower for word in ["book", "reserve", "table", "reservation"]):
            intent = "reservation"
        elif any(word in command_lower for word in ["hello", "hi", "hey"]):
            intent = "greeting"
        else:
            intent = "other"
        
        # Simple restaurant name extraction
        restaurant_match = {"found": False, "name": "", "confidence": 0.0}
        for restaurant in available_restaurants:
            name = restaurant.get("name", "").lower()
            if name in command_lower or any(word in command_lower for word in name.split()):
                restaurant_match = {
                    "found": True,
                    "name": restaurant.get("name"),
                    "confidence": 0.7,
                    "restaurant_id": restaurant.get("id"),
                    "restaurant_data": restaurant
                }
                break
        
        return {
            "intent": intent,
            "confidence": 0.6,
            "restaurant_match": restaurant_match,
            "response_message": "I understood your request. Let me help you with that.",
            "action_required": "book_table" if intent == "reservation" else "provide_info"
        }
    
    async def generate_conversation_response(self, user_message: str, context: Dict = None) -> str:
        """Generate a conversational response for general chat"""
        if not self.enabled:
            return "I'm here to help you make restaurant reservations. Try saying 'book a table at [restaurant name]'."
        
        try:
            prompt = f"""
You are a friendly restaurant reservation assistant. The user said: "{user_message}"

Respond naturally and helpfully. Keep responses concise and focused on restaurant reservations.
If they're asking for help, explain how to make reservations using voice commands.

Response:
"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating conversation response: {e}")
            return "I'm here to help you with restaurant reservations. How can I assist you today?"

# Global instance
gemini_service = GeminiService()