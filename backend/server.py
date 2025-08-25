# ClinicHub - Absolute Minimal Backend for Deployment Success
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

print("🚀 ClinicHub Ultra-Minimal Deployment Starting")

# FastAPI setup
app = FastAPI(title="ClinicHub API")

# CORS - Allow everything
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple models
class UserLogin(BaseModel):
    username: str
    password: str

# Mock authentication for demonstration
DEMO_USERS = {
    "admin": {
        "password": "admin123",
        "id": "demo-admin",
        "username": "admin",
        "email": "admin@clinichub.com",
        "first_name": "Demo",
        "last_name": "Administrator",
        "role": "admin",
        "is_active": True
    }
}

# Routes
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "database": "mock", 
        "timestamp": "2025-01-17T12:00:00Z",
        "environment": "DEMO"
    }

@app.post("/api/auth/init-admin")
async def init_admin():
    return {"message": "Demo admin ready", "status": "success"}

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    print(f"🔧 [LOGIN] Attempt: {credentials.username}")
    
    if credentials.username in DEMO_USERS:
        user_data = DEMO_USERS[credentials.username]
        if credentials.password == user_data["password"]:
            print(f"✅ [LOGIN] Success: {credentials.username}")
            return {
                "access_token": "demo-token-12345",
                "token_type": "bearer",
                "user": user_data
            }
    
    print(f"❌ [LOGIN] Failed: {credentials.username}")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/api/auth/me")
async def get_me():
    return DEMO_USERS["admin"]

@app.get("/api/patients")
async def get_patients():
    return [
        {
            "id": "demo-patient-1",
            "name": [{"given": ["John"], "family": "Doe"}],
            "email": "john.doe@example.com",
            "phone": "555-0123"
        },
        {
            "id": "demo-patient-2", 
            "name": [{"given": ["Jane"], "family": "Smith"}],
            "email": "jane.smith@example.com",
            "phone": "555-0456"
        }
    ]

@app.get("/api/employees")
async def get_employees():
    return [
        {
            "id": "emp-001",
            "employee_id": "EMP-001",
            "first_name": "Dr. Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@clinichub.com",
            "role": "doctor",
            "department": "Internal Medicine",
            "is_active": True
        },
        {
            "id": "emp-002",
            "employee_id": "EMP-002",
            "first_name": "Lisa",
            "last_name": "Chen", 
            "email": "lisa.chen@clinichub.com",
            "role": "nurse",
            "department": "General",
            "is_active": True
        }
    ]

@app.get("/api/inventory") 
async def get_inventory():
    return [
        {
            "id": "inv-001",
            "item_name": "Digital Thermometer",
            "category": "Medical Equipment",
            "current_stock": 25,
            "min_stock_level": 5,
            "unit_cost": 29.99,
            "supplier": "MedSupply Inc"
        },
        {
            "id": "inv-002",
            "item_name": "Disposable Gloves",
            "category": "Medical Supplies", 
            "current_stock": 150,
            "min_stock_level": 50,
            "unit_cost": 12.50,
            "supplier": "HealthCare Supplies"
        }
    ]

@app.get("/api/quality-measures")
async def get_quality_measures():
    return [
        {
            "id": "qm-001",
            "name": "Diabetes HbA1c Control",
            "description": "Percentage of patients with diabetes who have HbA1c < 7%",
            "category": "Diabetes Care",
            "measure_type": "outcome",
            "target_value": 80,
            "current_value": 85,
            "status": "met"
        },
        {
            "id": "qm-002",
            "name": "Blood Pressure Control",
            "description": "Percentage of patients with controlled blood pressure",
            "category": "Cardiovascular",
            "measure_type": "outcome", 
            "target_value": 75,
            "current_value": 78,
            "status": "met"
        }
    ]

@app.get("/api/auth/synology-status")
async def synology_status():
    return {"enabled": False, "configured": False}

# Root route
@app.get("/")
async def root():
    return {
        "message": "ClinicHub Demo API",
        "status": "running",
        "modules": 16,
        "lines_of_code": 11726
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)