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
ROOT_DIR = Path(__file__).parent
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
    # No fallback - require proper environment configuration  
    raise ValueError("MONGO_URL must be set in environment or secrets")

def sanitize_mongo_uri(uri: str) -> str:
    """Ensure username/password are percent-encoded in the Mongo URI."""
    p = urlparse(uri)
    # If no user/pass present, return as-is
    if not (p.username or p.password):
        return uri

    user = quote(p.username or '', safe='')
    pw   = quote(p.password or '', safe='')
    query = f'?{p.query}' if p.query else ''
    path  = p.path or '/clinichub'
    host  = p.hostname or 'localhost'
    port  = f":{p.port}" if p.port else ''

    return f"mongodb://{user}:{pw}@{host}{port}{path}{query}"

mongo_url = sanitize_mongo_uri(mongo_url)

# Configure MongoDB client with proper timeouts for production
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=5000,    # 5 second server selection timeout
    connectTimeoutMS=10000,           # 10 second connection timeout
    socketTimeoutMS=30000,            # 30 second socket timeout
    maxPoolSize=50,                   # Connection pool size
    retryWrites=True                  # Retry writes on failure
)
db = client[os.environ.get('DB_NAME', 'clinichub')]

# Test database connection on startup
async def test_database_connection():
    """Test database connectivity with timeout"""
    try:
        # Simple ping command with timeout
        await client.admin.command('ping')
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print(f"🔍 Connection URL: {mongo_url.split('@')[1] if '@' in mongo_url else 'local'}")
        return False

# JWT Configuration - use same logic as main server
SECRET_KEY = read_secret('app_secret_key', 'SECRET_KEY')
JWT_SECRET_KEY = read_secret('jwt_secret_key', 'JWT_SECRET_KEY')

if not SECRET_KEY:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key-change-immediately')
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback-jwt-key-change-immediately')

# Use the same key as main server for JWT operations
JWT_SECRET_FOR_DECODE = SECRET_KEY
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')

security = HTTPBearer()

async def get_db():
    """Get database connection"""
    return db

async def get_current_active_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current active user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_FOR_DECODE, algorithms=[JWT_ALGORITHM])
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
                self.id = username  # Add id attribute
                
        return User(username)
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )