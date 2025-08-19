from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uvicorn
import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid

load_dotenv()

app = FastAPI(title="ClinicHub", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
try:
    MONGO_URL = os.environ.get('MONGO_URL')
    DB_NAME = os.environ.get('DB_NAME', 'clinichub')
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    client.admin.command('ping')
    print(f"✅ Connected to MongoDB: {DB_NAME}")
except Exception as e:
    print(f"❌ Database error: {e}")
    db = None

# Models
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: str
    gender: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Routes
@app.get("/")
async def root():
    return {"message": "ClinicHub Medical Practice Management", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "ClinicHub", "database": "connected" if db else "disconnected"}

@app.post("/api/auth/login")
async def login(credentials: LoginRequest):
    if credentials.username == "admin" and credentials.password == "admin123":
        return {"access_token": "demo-token", "token_type": "bearer", "user_id": "admin", "role": "administrator"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/patients")
async def get_patients():
    if not db:
        return {"patients": [], "count": 0}
    try:
        patients = list(db.patients.find({}, {"_id": 0}).limit(50))
        return {"patients": patients, "count": len(patients)}
    except Exception as e:
        return {"patients": [], "count": 0, "error": str(e)}

@app.post("/api/patients")
async def create_patient(patient: PatientCreate):
    if not db:
        raise HTTPException(status_code=500, detail="Database unavailable")
    
    patient_doc = {
        "id": f"pat_{str(uuid.uuid4())[:8]}",
        "mrn": f"MRN{str(uuid.uuid4().int)[:6]}",
        **patient.dict(),
        "created_at": datetime.utcnow()
    }
    
    db.patients.insert_one(patient_doc)
    patient_doc.pop("_id", None)
    return patient_doc

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    if not db:
        return {"total_patients": 0, "total_appointments": 0, "total_employees": 0}
    
    try:
        return {
            "total_patients": db.patients.count_documents({}),
            "total_appointments": db.appointments.count_documents({}),
            "total_employees": db.employees.count_documents({}),
            "appointments_today": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    except:
        return {"total_patients": 0, "total_appointments": 0, "total_employees": 0}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
