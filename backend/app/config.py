import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017/"

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
# Support both ACCESS_TOKEN_EXPIRE_MINUTES and legacy JWT_EXPIRATION_MINUTES
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", os.getenv("JWT_EXPIRATION_MINUTES", "30")))

# WhatsApp webhook verification (Meta Cloud legacy support)
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

# OpenAI API settings
# OpenAI API settings (legacy)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Gemini API settings (preferred)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Twilio WhatsApp settings (required for WhatsApp messaging)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

# WhatsApp template settings (used for production send to new recipients)
# Provide an approved template body via env for initiating conversations.
# Example: "Hello {{1}}, your daily recipe plan is ready."
WHATSAPP_TEMPLATE_HELLO = os.getenv("WHATSAPP_TEMPLATE_HELLO", "")
WHATSAPP_TEMPLATE_LANG = os.getenv("WHATSAPP_TEMPLATE_LANG", "en_US")