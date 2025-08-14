# ClinicHub Quick Start Guide

## 🚀 Fast Installation (5 minutes)

### Prerequisites
- Docker and Docker Compose installed
- 8GB+ RAM recommended

### 1. Clone Repository
```bash
git clone https://github.com/clinichub-solace/alpine-chub.git
cd alpine-chub
```

### 2. Start Services
```bash
# Start all services
docker compose up -d

# Check status
docker compose ps
```

### 3. Initialize Admin User
```bash
# Wait 30 seconds for services to start
sleep 30

# Initialize admin user
curl -X POST "http://localhost:8001/api/auth/init-admin"
```

### 4. Access System
- **🏥 Frontend Dashboard**: http://localhost:3000
- **🔧 API Documentation**: http://localhost:8001/docs
- **👤 Login**: admin / admin123

## ✅ Expected Results

All containers should show "Up" status:
```
clinichub-backend    Up (healthy)
clinichub-frontend   Up (healthy) 
clinichub-mongodb    Up
```

## 🔧 Troubleshooting

### Backend Won't Start
```bash
# Check logs
docker compose logs backend

# Common fix - restart
docker compose restart backend
```

### Frontend Build Issues
```bash
# Rebuild frontend
docker compose build frontend --no-cache
```

### Database Issues
```bash
# Reset database
docker compose down -v
docker compose up -d
```

## 🏥 Features Available

- **Patient/EHR Management** - Complete patient records
- **Electronic Prescribing** - FHIR-compliant eRx system
- **Inventory Management** - Medical supplies tracking
- **Employee Management** - Staff profiles and scheduling
- **Financial Management** - Income/expense tracking
- **Smart Forms** - Dynamic form builder
- **Clinical Templates** - Standardized care protocols
- **Quality Measures** - Performance tracking
- **Telehealth** - Video consultations
- **And 8+ more modules**

## 📞 Support

- **Logs**: `docker compose logs`
- **Restart**: `docker compose restart`
- **Stop**: `docker compose down`
- **Update**: `git pull && docker compose up -d --build`