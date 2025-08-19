# ClinicHub Troubleshooting Guide

## 🚨 Most Common Issues & Solutions

### 1. **NETWORK ERROR / LOGIN LOOP**

**Symptoms:**
- Frontend shows "Network Error" on login
- Browser console shows connection to `localhost:8001` instead of your IP
- Login stays in "Signing in..." loop

**Root Cause:** React not picking up environment variables properly

**Solution:**
```bash
# 1. Verify the hardcoded fallback is in the frontend code
head -15 frontend/src/App.js

# Should show:
# const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://YOUR_IP:8001';

# 2. If missing, add the hardcoded fallback and rebuild
docker compose down
docker system prune -f
docker compose build --no-cache
docker compose up -d
```

### 2. **DOCKER CONTAINER NOT UPDATING**

**Symptoms:**
- Made code changes but they don't take effect
- Container shows old code when inspected
- Environment variables not updating

**Solution - Nuclear Rebuild:**
```bash
# Stop everything
docker compose down -v

# Clean all Docker artifacts
docker system prune -a -f

# Remove specific images if needed
docker rmi $(docker images | grep frontend | awk '{print $3}') 2>/dev/null || true

# Pull latest code
git stash  # if local changes
git pull origin main --force

# Rebuild from scratch
docker compose build --no-cache
docker compose up -d
```

### 3. **BACKEND 404 ERROR**

**Symptoms:**
- Backend returns 404 when accessing root URL
- API endpoints work but base URL fails

**Solution:** Ensure root route exists in `backend/server.py`:
```python
@app.get("/")
async def root():
    return {
        "message": "ClinicHub API is running", 
        "status": "healthy", 
        "version": "1.0.0",
        "docs": "/docs",
        "api_endpoints": "/api"
    }
```

### 4. **NO SPACE LEFT ON DEVICE**

**Symptoms:**
- Docker build fails with "no space left on device"
- Containers won't start due to disk space

**Solution:**
```bash
# Check disk usage
df -h

# Clean Docker system
docker system prune -a -f
docker volume prune -f

# Remove build artifacts
rm -rf frontend/node_modules
rm -rf frontend/build
rm -rf backend/__pycache__

# Remove log files
find . -name "*.log" -delete
```

### 5. **GIT MERGE CONFLICTS**

**Symptoms:**
- `git pull` fails with merge conflict errors
- Can't update to latest code

**Solution:**
```bash
# Force update (WARNING: loses local changes)
git stash
git pull origin main --force

# Or reset completely
git reset --hard HEAD
git pull origin main --force
```

### 6. **MONGODB UNHEALTHY**

**Symptoms:**
- MongoDB shows as "unhealthy" in docker ps
- Login works but database operations fail

**Solution:**
```bash
# Restart MongoDB
docker compose restart mongodb
sleep 30

# Reinitialize admin user
curl -X POST "http://YOUR_IP:8001/api/auth/init-admin"

# Test connection
curl -X POST "http://YOUR_IP:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## 🔍 **Verification Steps**

### Verify Frontend Fix Applied:
```bash
# Check code in container
docker exec clinichub-frontend cat /app/src/App.js | head -15

# Should show hardcoded fallback URL
```

### Verify Backend Working:
```bash
# Test root endpoint
curl http://YOUR_IP:8001/

# Should return JSON with "ClinicHub API is running"
```

### Verify Services Healthy:
```bash
docker compose ps

# All should show "Up (healthy)" except MongoDB may show "unhealthy" but still work
```

## 🚀 **Success Indicators**

- ✅ Frontend loads at http://YOUR_IP:3000
- ✅ Backend returns JSON at http://YOUR_IP:8001
- ✅ Login works with admin/admin123
- ✅ No "Network Error" messages
- ✅ Browser console shows correct backend URL

## 📞 **Still Having Issues?**

1. **Check browser console** for specific error messages
2. **Check Docker logs**: `docker compose logs frontend` and `docker compose logs backend`
3. **Verify IP address** in all configurations matches your actual IP
4. **Try the nuclear rebuild option** if all else fails

Remember: The most common issue is the frontend not updating with new code. When in doubt, use the nuclear rebuild approach!