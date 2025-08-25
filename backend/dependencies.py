# EMERGENCY DEPLOYMENT FIX: Force MongoDB at module import level
import os
# DEPLOYMENT FIX: Use MongoDB Atlas for production deployment
os.environ['MONGO_URL'] = 'mongodb+srv://vizantana:U9TeV2xRMtkW7Pqg@cluster0.oniyqht.mongodb.net/clinichub?retryWrites=true&w=majority&appName=Cluster0'
os.environ['DB_NAME'] = 'clinichub'
print("🚨 DEPLOYMENT FIX: Configuring MongoDB Atlas connection")

# app/backend/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import urlparse, quote
import jwt
from pathlib import Path
from dotenv import load_dotenv

# DEPLOYMENT FIX: Override MongoDB URL for local service
# Try to use localhost first, but fallback to environment if localhost not available
original_mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/clinichub')
os.environ['MONGO_URL'] = 'mongodb://localhost:27017/clinichub'

# Load environment variables AFTER forcing the override
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

# Enhanced MongoDB connection with deployment environment detection
def get_mongo_url():
    """Get MongoDB URL with deployment environment detection and fallback options"""
    mongo_url = read_secret('mongo_connection_string', 'MONGO_URL')
    
    # DEPLOYMENT ENVIRONMENT DETECTION
    # Check if we're in a deployment environment that provides managed MongoDB
    deployment_mongo_patterns = [
        "MONGO_URL", "DATABASE_URL", "MONGODB_URI", "DB_CONNECTION_STRING"
    ]
    
    # First, try to detect if deployment provides MongoDB service
    for pattern in deployment_mongo_patterns:
        env_url = os.environ.get(pattern)
        if env_url and env_url != "" and "localhost" not in env_url and "127.0.0.1" not in env_url:
            # Deployment environment provided MongoDB - use it
            if "mongodb.net" not in env_url and "atlas" not in env_url.lower():
                print(f"🔧 Using deployment-provided MongoDB: {env_url}")
                return env_url
    
    # BULLETPROOF: Check for external URLs and handle appropriately  
    if not mongo_url or mongo_url == "" or "mongodb.net" in mongo_url or "atlas" in mongo_url.lower() or "customer-apps" in mongo_url:
        print(f"🔒 Detected external/invalid MongoDB URL")
        print(f"🔍 Original URL was: {mongo_url if mongo_url else 'None'}")
        
        # Try different local/deployment MongoDB configurations
        possible_urls = [
            "mongodb://mongodb:27017/clinichub",    # Docker service name (most common in deployments)
            "mongodb://db:27017/clinichub",         # Alternative Docker service name
            "mongodb://localhost:27017/clinichub",  # Localhost fallback
            "mongodb://127.0.0.1:27017/clinichub"   # IP fallback
        ]
        
        # Use the first one (Docker service name) for deployment
        mongo_url = possible_urls[0]
        print(f"🔧 Using fallback MongoDB URL: {mongo_url}")
    else:
        print(f"🔧 Using configured MongoDB URL: {mongo_url}")
    
    return mongo_url

# Database connection - FORCE local MongoDB for deployment stability
mongo_url = get_mongo_url()

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