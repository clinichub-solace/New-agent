from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# Initialize FastAPI app
app = FastAPI(
    title="ClinicHub - Medical Practice Management System",
    version="1.0.0",
    description="Comprehensive medical practice management system for Alpine Docker environments"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'clinichub-jwt-secret-key-2024-very-secure')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database connection
try:
    MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://admin:ClinicHub2024!Secure@mongodb:27017/clinichub?authSource=admin')
    DB_NAME = os.environ.get('DB_NAME', 'clinichub')
    
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Test connection
    client.admin.command('ping')
    print(f"✅ Connected to MongoDB database: {DB_NAME}")
    
except Exception as e:
    print(f"❌ Database connection error: {e}")
    db = None

# Pydantic Models
class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    date_of_birth: str
    gender: str
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class PatientResponse(BaseModel):
    id: str
    mrn: str
    first_name: str
    last_name: str
    email: str
    phone: str
    date_of_birth: str
    gender: str
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    created_at: datetime

class AppointmentCreate(BaseModel):
    patient_id: str
    provider_id: str
    appointment_date: str
    appointment_time: str
    reason: str
    status: Optional[str] = "scheduled"

class AppointmentResponse(BaseModel):
    id: str
    patient_id: str
    provider_id: str
    appointment_date: str
    appointment_time: str
    reason: str
    status: str
    created_at: datetime

class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    role: str
    specialty: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None

class EmployeeResponse(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    role: str
    specialty: Optional[str] = None
    email: str
    phone: Optional[str] = None
    created_at: datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str

# Utility Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Routes
@app.get("/")
async def root():
    return {
        "message": "ClinicHub Medical Practice Management System",
        "version": "1.0.0",
        "status": "running",
        "environment": "Alpine Docker",
        "database": "connected" if db is not None else "disconnected"
    }

@app.get("/api/health")
async def health_check():
    db_status = "connected"
    try:
        if db:
            client.admin.command('ping')
    except:
        db_status = "disconnected"
    
    return {
        "status": "healthy",
        "service": "ClinicHub",
        "version": "1.0.0",
        "database": db_status,
        "environment": "Alpine Docker",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    # Default admin credentials for initial setup
    if credentials.username == "admin" and credentials.password == "admin123":
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": "admin", "role": "administrator"}, 
            expires_delta=access_token_expires
        )
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_id="admin",
            role="administrator"
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.get("/api/patients", response_model=List[PatientResponse])
async def get_patients():
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        patients = list(db.patients.find({}, {"_id": 0}).limit(50))
        return patients
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching patients: {str(e)}")

@app.post("/api/patients", response_model=PatientResponse)
async def create_patient(patient: PatientCreate):
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        # Generate unique identifiers
        patient_id = f"pat_{str(uuid.uuid4())[:8]}"
        mrn = f"MRN{str(uuid.uuid4().int)[:6]}"
        
        # Create patient document
        patient_doc = {
            "id": patient_id,
            "mrn": mrn,
            **patient.dict(),
            "created_at": datetime.utcnow()
        }
        
        # Insert into database
        db.patients.insert_one(patient_doc)
        
        # Return created patient
        patient_doc.pop("_id", None)  # Remove MongoDB _id
        return PatientResponse(**patient_doc)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating patient: {str(e)}")

@app.get("/api/appointments", response_model=List[AppointmentResponse])
async def get_appointments():
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        appointments = list(db.appointments.find({}, {"_id": 0}).limit(50))
        return appointments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching appointments: {str(e)}")

@app.post("/api/appointments", response_model=AppointmentResponse)
async def create_appointment(appointment: AppointmentCreate):
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        appointment_id = f"apt_{str(uuid.uuid4())[:8]}"
        
        appointment_doc = {
            "id": appointment_id,
            **appointment.dict(),
            "created_at": datetime.utcnow()
        }
        
        db.appointments.insert_one(appointment_doc)
        
        appointment_doc.pop("_id", None)
        return AppointmentResponse(**appointment_doc)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating appointment: {str(e)}")

@app.get("/api/employees", response_model=List[EmployeeResponse])
async def get_employees():
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        employees = list(db.employees.find({}, {"_id": 0}).limit(50))
        return employees
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

@app.post("/api/employees", response_model=EmployeeResponse)
async def create_employee(employee: EmployeeCreate):
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        employee_id = f"emp_{str(uuid.uuid4())[:8]}"
        
        employee_doc = {
            "employee_id": employee_id,
            **employee.dict(),
            "created_at": datetime.utcnow()
        }
        
        db.employees.insert_one(employee_doc)
        
        employee_doc.pop("_id", None)
        return EmployeeResponse(**employee_doc)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating employee: {str(e)}")

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    if not db:
        raise HTTPException(status_code=500, detail="Database connection error")
    
    try:
        stats = {
            "total_patients": db.patients.count_documents({}),
            "total_appointments": db.appointments.count_documents({}),
            "total_employees": db.employees.count_documents({}),
            "appointments_today": db.appointments.count_documents({
                "appointment_date": datetime.utcnow().strftime("%Y-%m-%d")
            }),
            "timestamp": datetime.utcnow().isoformat()
        }
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

# Initialize default admin user on startup
@app.on_event("startup")
async def startup_event():
    if db:
        try:
            # Create default admin user if it doesn't exist
            admin_exists = db.users.find_one({"username": "admin"})
            if not admin_exists:
                admin_user = {
                    "id": "user_admin",
                    "username": "admin",
                    "password": hash_password("admin123"),
                    "role": "administrator",
                    "email": "admin@clinichub.local",
                    "created_at": datetime.utcnow()
                }
                db.users.insert_one(admin_user)
                print("✅ Default admin user created (admin/admin123)")
            
            print("✅ ClinicHub backend started successfully")
        except Exception as e:
            print(f"⚠️  Startup warning: {e}")

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=os.environ.get('HOST', '0.0.0.0'), 
        port=int(os.environ.get('PORT', 8001)),
        log_level="info"
    )