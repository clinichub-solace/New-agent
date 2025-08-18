# app/backend/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import urlparse, quote
import jwt
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

def read_secret(secret_name: str, fallback_env: str = None) -> str:
    """Read secret from file or environment"""
    secret_file = f'/run/secrets/{secret_name}'
    env_file = os.environ.get(f'{fallback_env}_FILE') if fallback_env else None
    
    # Try Docker secret first
    if os.path.exists(secret_file):
        with open(secret_file, 'r') as f:
            return f.read().strip()
    
    # Try _FILE environment variable  
    if env_file and os.path.exists(env_file):
        with open(env_file, 'r') as f:
            return f.read().strip()
    
    # Fall back to direct environment variable
    if fallback_env:
        return os.environ.get(fallback_env, '')
    
    return ''

# Database connection
mongo_url = read_secret('mongo_connection_string', 'MONGO_URL')
if not mongo_url:
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/clinichub')

client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'clinichub')]

# JWT Configuration - use same logic as main server
JWT_SECRET_KEY = read_secret('jwt_secret_key', 'JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-key-change-immediately')

JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')

security = HTTPBearer()

async def get_current_active_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current active user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # For simplicity, return a user object
        class User:
            def __init__(self, username):
                self.username = username
                
        return User(username)
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )