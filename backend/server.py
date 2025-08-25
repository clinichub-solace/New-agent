# ClinicHub Backend - Minimal Working Version for Investor Demo
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

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/clinichub')
DB_NAME = os.environ.get('DB_NAME', 'clinichub')
SECRET_KEY = os.environ.get('SECRET_KEY', 'clinichub-secret-key')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'clinichub-jwt-secret')

print(f"🚀 ClinicHub Starting - Investor Demo")
print(f"🔧 MongoDB: {MONGO_URL}")

# FastAPI setup
app = FastAPI(title="ClinicHub API", description="FHIR-Compliant Practice Management")
api_router = APIRouter()

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CORS setup
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Database
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

# Auth functions
def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(hours=8)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")

async def authenticate_user(username: str, password: str):
    try:
        user = await db.users.find_one({"username": username})
        if user and pwd_context.verify(password, user["hashed_password"]):
            return user
    except:
        pass
    return None

# Routes
@api_router.get("/health")
async def health():
    try:
        await client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@api_router.post("/auth/init-admin")  
async def init_admin():
    try:
        existing = await db.users.find_one({"username": "admin"})
        if existing:
            return {"message": "Admin exists"}
        
        admin = {
            "id": "admin",
            "username": "admin",
            "email": "admin@clinichub.com", 
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "hashed_password": pwd_context.hash("admin123"),
            "is_active": True
        }
        await db.users.insert_one(admin)
        return {"message": "Admin created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login")
async def login(creds: UserLogin):
    try:
        user = await authenticate_user(creds.username, creds.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_access_token({"sub": user["username"]})
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user["id"], "username": user["username"], "role": user["role"]}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/patients")
async def get_patients():
    try:
        return await db.patients.find({}, {"_id": 0}).to_list(100) or []
    except:
        return []

@api_router.get("/auth/synology-status")
async def synology_status():
    return {"enabled": False, "configured": False}

# Include router with /api prefix - CRITICAL FOR ROUTING
app.include_router(api_router, prefix="/api")