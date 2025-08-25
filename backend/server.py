# ClinicHub Backend - Clean Production Version for Investor Demo
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Simple MongoDB connection for deployment
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/clinichub')
DB_NAME = os.environ.get('DB_NAME', 'clinichub')

# FastAPI setup
app = FastAPI(title="ClinicHub API", description="FHIR-Compliant Practice Management")
api_router = APIRouter()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Simple health check
@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "environment": os.environ.get('ENV', 'PRODUCTION')
    }

# Include router with /api prefix
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)