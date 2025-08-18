# ClinicHub Installation Guide

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- 8GB+ RAM recommended
- 20GB+ free disk space

## Quick Installation

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

### 3. Initialize System
```bash
# Wait for services to start (30 seconds)
sleep 30

# Initialize admin user
curl -X POST "http://localhost:8001/api/auth/init-admin"
```

### 4. Access System
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8001/docs
- **Login**: admin / admin123

## Service Management

### Check Status
```bash
docker compose ps
```

### View Logs
```bash
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs frontend
docker compose logs mongodb
```

### Restart Services
```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
```

### Stop Services
```bash
docker compose down
```

### Update System
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build
```

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
docker compose logs backend

# Restart backend
docker compose restart backend
```

### Frontend Build Issues
```bash
# Rebuild frontend
docker compose build frontend --no-cache
docker compose up -d frontend
```

### Database Issues
```bash
# Reset database
docker compose down -v
docker compose up -d
```

### Health Checks
```bash
# Test backend
curl http://localhost:8001/health

# Test frontend
curl http://localhost:3000
```

## Configuration

### Environment Variables
- Backend: `backend/.env`
- Frontend: `frontend/.env`

### MongoDB
- Default: mongo:4.4 (stable)
- Data: Persistent volume `mongodb_data`

### Ports
- Frontend: 3000
- Backend: 8001
- MongoDB: 27017

## Features

### Comprehensive Practice Management
- Patient/EHR Management
- Electronic Prescribing (eRx)
- Inventory Management
- Employee Management
- Financial Management
- Smart Forms
- Clinical Templates
- Quality Measures
- Telehealth
- And more...

## Support

For issues:
1. Check logs: `docker compose logs`
2. Restart services: `docker compose restart`
3. Check GitHub issues
4. Contact support