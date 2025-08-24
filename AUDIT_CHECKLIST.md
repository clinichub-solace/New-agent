# 🔍 CLINICHUB AUDIT CHECKLIST - NEW AGENT

## ⚡ CRITICAL SEARCH COMMANDS

### **1. Find All MongoDB Connections**
```bash
grep -r "mongodb://" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "MongoClient\|AsyncIOMotorClient" . --exclude-dir=node_modules --exclude-dir=.git
```

### **2. Find All Backend URL References** 
```bash
grep -r "REACT_APP_BACKEND_URL" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "localhost:8001\|127.0.0.1:8001" . --exclude-dir=node_modules --exclude-dir=.git
```

### **3. Find External Domain References**
```bash
grep -r "\.net\|\.com\|https://" . --exclude-dir=node_modules --exclude-dir=.git --exclude="*.md"
```

### **4. Find API Route Definitions**
```bash
grep -r "@app\.\|router\.\|api_router" backend/ --include="*.py"
```

## 📋 FILE-BY-FILE CHECKLIST

### **Critical Files to Verify:**

**Frontend:**
- [ ] `/frontend/.env` → REACT_APP_BACKEND_URL=/api
- [ ] `/frontend/.env.production` → REACT_APP_BACKEND_URL=/api  
- [ ] `/frontend/src/api/axios.js` → baseURL uses environment variable
- [ ] `/frontend/src/App.js` → Uses `api` instance, not raw `axios`

**Backend:**
- [ ] `/backend/.env` → MONGO_URL=mongodb://localhost:27017/clinichub
- [ ] `/backend/server.py` → MongoDB override logic working
- [ ] `/backend/dependencies.py` → MongoDB override logic working
- [ ] All routes have `/api` prefix

**Configuration:**
- [ ] No hardcoded URLs in any config files
- [ ] Environment variables used consistently
- [ ] No external database connections

## ✅ VALIDATION TESTS

### **1. Backend API Test**
```bash
curl http://localhost:8001/api/ping
```
**Expected**: `{"message":"pong","timestamp":"..."}`

### **2. Database Test**  
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
**Expected**: JWT token response

### **3. Frontend Test**
- Load frontend in browser
- Test login with admin/admin123  
- Check browser console for errors
- Verify no external MongoDB errors

## 🚨 RED FLAGS TO FIX
- Any reference to `mongodb.net`
- Any reference to `customer-apps-pri`
- Hardcoded `localhost:8001` or `127.0.0.1:8001`
- Raw `axios` calls instead of `api` instance
- Routes without `/api` prefix
- `[Errno 111] Connection refused` errors

## 🎯 SUCCESS INDICATORS
- ✅ Clean login without errors
- ✅ All API calls use `/api/*` paths
- ✅ MongoDB connects to localhost only
- ✅ No external URL references
- ✅ Stable deployment environment

**Focus on systematic fixing - one category at a time!** 🔧