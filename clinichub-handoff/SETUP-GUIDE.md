# 🚀 ClinicHub 5-Minute Setup Guide

## Prerequisites
- **Python 3.11+** 
- **Node.js 18.0+**
- **MongoDB 6.0+**
- **Git** (optional)

## 🎯 Quick Start (5 Minutes)

### Step 1: Environment Setup (1 minute)
```bash
# Clone or extract ClinicHub
cd clinichub-handoff

# Copy environment files
cp .env.example backend/.env
cp .env.example frontend/.env

# Edit backend/.env to set your MongoDB connection
# Default: MONGO_URL=mongodb://localhost:27017/clinichub
```

### Step 2: Database Setup (1 minute)
```bash
# Start MongoDB (if not running)
mongod --dbpath ./data/db

# Initialize database with sample data
mongosh mongodb://localhost:27017/clinichub < database/init_mongodb.js
```

### Step 3: Backend Setup (1 minute)
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start backend server
python server.py
```

### Step 4: Frontend Setup (1 minute)
```bash
cd frontend

# Install Node dependencies  
npm install

# Start development server
npm start
```

### Step 5: Verification (1 minute)
```bash
# Test backend health
curl http://localhost:8001/api/health

# Initialize admin user
curl -X POST http://localhost:8001/api/auth/init-admin

# Access application
open http://localhost:3000
```

## 🔐 Default Credentials
- **Username**: admin
- **Password**: admin123

## 📋 Available Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/init-admin` - Initialize admin user
- `GET /api/auth/me` - Get current user

### Patient Management
- `GET /api/patients` - List patients
- `POST /api/patients` - Create patient
- `GET /api/patients/{id}` - Get patient details

### Clinical Data
- `POST /api/soap-notes` - Create SOAP note
- `POST /api/vital-signs` - Record vital signs
- `POST /api/allergies` - Add allergy
- `GET /api/icd10/search` - Search ICD-10 codes

### Practice Management
- `GET /api/employees` - List employees  
- `POST /api/time-tracking/clock-in` - Clock in
- `POST /api/receipts` - Create receipt
- `GET /api/inventory` - List inventory

## 🐛 Troubleshooting

### MongoDB Connection Issues
```bash
# Check MongoDB is running
mongosh --eval "db.adminCommand('ismaster')"

# Verify database exists
mongosh clinichub --eval "db.stats()"
```

### Backend Not Starting
```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep fastapi

# Check logs
tail -f backend/logs/error.log
```

### Frontend Build Issues
```bash
# Check Node version
node --version  # Should be 18.0+

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 🎉 Success Indicators

✅ **Backend**: http://localhost:8001/api/health returns `{"status": "healthy"}`  
✅ **Frontend**: http://localhost:3000 shows ClinicHub login page  
✅ **Database**: `mongosh clinichub --eval "db.users.findOne()"` returns admin user  
✅ **Login**: admin/admin123 credentials work in web interface  

## 🏥 System Overview

**16 Complete Modules:**
- Patient Management & EHR
- Appointment Scheduling  
- Clinical Documentation (SOAP)
- Medication Management
- Lab Orders & Results
- Quality Measures
- Employee Management
- Time Tracking & Payroll
- Inventory Management
- Financial Management
- Insurance Verification
- Telehealth Platform
- Patient Portal
- Document Management
- Communication Center
- System Administration

**Ready for enterprise healthcare deployment!** 🚀