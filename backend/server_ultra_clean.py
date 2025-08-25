# ClinicHub Clean Backend - Authentication Only for Deployment
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

print("🚀 ClinicHub Clean Deployment Starting")

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configuration - FORCE localhost MongoDB
MONGO_URL = 'mongodb://localhost:27017/clinichub'
DB_NAME = 'clinichub'
SECRET_KEY = os.environ.get('SECRET_KEY', 'clinichub-secret-key')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'clinichub-jwt-secret')

print(f"🔧 MongoDB: {MONGO_URL}")
print(f"📁 Database: {DB_NAME}")

# FastAPI setup
app = FastAPI(title="ClinicHub API", description="FHIR-Compliant Practice Management")
api_router = APIRouter()

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection - SIMPLE and CLEAN
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Models
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class User(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool = True

# Authentication functions
def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(hours=8)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")

async def authenticate_user(username: str, password: str):
    print(f"🔧 [AUTH] Authenticating user: {username}")
    try:
        user = await db.users.find_one({"username": username})
        if user and pwd_context.verify(password, user["hashed_password"]):
            print(f"✅ [AUTH] User authenticated successfully")
            return user
        else:
            print(f"❌ [AUTH] Authentication failed")
            return None
    except Exception as e:
        print(f"❌ [AUTH] Database error: {e}")
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication")
        user = await db.users.find_one({"username": username})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Routes
@api_router.get("/health")
async def health_check():
    try:
        await client.admin.command('ping')
        return {
            "status": "healthy", 
            "database": "connected", 
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.environ.get('ENV', 'PRODUCTION')
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database": "disconnected", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@api_router.post("/auth/init-admin")
async def init_admin():
    try:
        existing = await db.users.find_one({"username": "admin"})
        if existing:
            return {"message": "Admin user already exists", "status": "success"}
        
        admin_user = {
            "id": "admin",
            "username": "admin", 
            "email": "admin@clinichub.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "hashed_password": pwd_context.hash("admin123"),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await db.users.insert_one(admin_user)
        return {"message": "Admin user created successfully", "status": "success"}
    except Exception as e:
        print(f"❌ [ADMIN] Error creating admin: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating admin: {str(e)}")

@api_router.post("/auth/login")
async def login(user_credentials: UserLogin):
    try:
        user = await authenticate_user(user_credentials.username, user_credentials.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token({"sub": user["username"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user.get("email", ""),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "role": user.get("role", "admin"),
                "is_active": user.get("is_active", True)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [LOGIN] Error during login: {e}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/patients")
async def get_patients(current_user: User = Depends(get_current_user)):
    try:
        patients = await db.patients.find({}, {"_id": 0}).to_list(100)
        return patients or []
    except Exception as e:
        print(f"❌ [PATIENTS] Error fetching patients: {e}")
        return []

@api_router.get("/auth/synology-status") 
async def synology_status():
    return {"enabled": False, "configured": False}

# Include router with /api prefix
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)