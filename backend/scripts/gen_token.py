import os
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv

if __name__ == "__main__":
    # Load backend .env
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRATION_MINUTES', '30'))

    sub = 'sai@gmail.com'
    expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {'sub': sub, 'exp': datetime.utcnow() + expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(token)