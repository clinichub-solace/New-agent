# ClinicHub Quick Start Guide

## 🚀 Fast Installation (5 minutes)

### Prerequisites
- Docker and Docker Compose installed
- 8GB+ RAM recommended
- 10GB+ free disk space

### 1. Clone Repository
```bash
git clone https://github.com/clinichub-solace/alpine-chub.git
cd alpine-chub
```

### 2. Start Services
```bash
# Start all services
docker compose up -d

# Check status (wait for all to be healthy)
docker compose ps

# If any containers fail, try nuclear rebuild:
# docker compose down -v
# docker system prune -f
# docker compose build --no-cache
# docker compose up -d
```

### 3. Initialize Admin User
```bash
# Wait 60 seconds for services to start
sleep 60

# Initialize admin user
curl -X POST "http://YOUR_IP:8001/api/auth/init-admin"

# Replace YOUR_IP with your actual IP (e.g., 192.168.0.243)
```

### 4. Verify Everything Works
```bash
# Test backend
curl http://YOUR_IP:8001/

# Should return: {"message": "ClinicHub API is running", "status": "healthy"}

# Test login
curl -X POST "http://YOUR_IP:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Should return JWT token
```

### 5. Access System
- **🏥 Frontend Dashboard**: http://YOUR_IP:3000
- **🔧 API Documentation**: http://YOUR_IP:8001/docs
- **👤 Login**: admin / admin123

## ✅ Expected Results

All containers should show "Up (healthy)" status:
```
NAME                 STATUS                    PORTS
clinichub-backend    Up X seconds (healthy)    0.0.0.0:8001->8001/tcp
clinichub-frontend   Up X seconds (healthy)    0.0.0.0:3000->3000/tcp  
clinichub-mongodb    Up X seconds             0.0.0.0:27017->27017/tcp
```

**Note:** MongoDB may show "unhealthy" but still work fine.

## 🚨 Common Issues

### Network Error on Login
If you see "Network Error" when logging in:

```bash
# Nuclear rebuild (fixes 90% of issues)
docker compose down -v
docker system prune -f
git pull origin main --force
docker compose build --no-cache
docker compose up -d
sleep 90

# Verify fix applied
docker exec clinichub-frontend cat /app/src/App.js | head -15
# Should show hardcoded fallback URL
```

### Backend 404 Error
If http://YOUR_IP:8001 returns 404:
```bash
# Check if root route exists
curl http://YOUR_IP:8001/
# Should return JSON, not 404
```

### No Space Left
If build fails with disk space error:
```bash
df -h  # Check space
docker system prune -a -f
rm -rf frontend/node_modules frontend/build
```

## 🔧 Troubleshooting

### View Logs
```bash
# Backend logs
docker compose logs backend

# Frontend logs  
docker compose logs frontend

# All logs
docker compose logs
```

### Restart Services
```bash
# Restart specific service
docker compose restart frontend

# Restart all
docker compose restart

# Nuclear option (complete reset)
docker compose down -v
docker compose up -d
```

### Update System
```bash
# Pull latest changes
git stash  # if you have local changes
git pull origin main --force

# Rebuild and restart
docker compose down
docker compose up -d --build
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
- **Nuclear Reset**: `docker compose down -v && docker system prune -f && docker compose up -d --build`

**🎯 Pro Tip:** When in doubt, use the nuclear rebuild option. It solves most issues by ensuring a completely fresh build.