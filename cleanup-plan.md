# ClinicHub Systematic Cleanup Plan

## PHASE A: IMMEDIATE REMOVALS (30 minutes)

### 1. Remove Synology Integration
```bash
# Backend cleanup:
- Remove synology-related routes from server.py
- Remove SYNOLOGY_* environment variables
- Clean synology configuration endpoints

# Frontend cleanup:
- Remove synology status calls from App.js
- Remove synology configuration UI
```

### 2. Remove Complex Communication Features
```bash
# Remove from App.js:
- sendFax function
- makeVoIPCall function  
- Advanced email functions
- Communication status checks
```

### 3. Remove Advanced Telehealth
```bash
# Keep: Basic appointment conversion
# Remove: Video sessions, waiting room, chat features
# Files: Remove telehealth session management
```

### 4. Remove External Lab Integration
```bash
# Keep: Basic lab orders
# Remove: External lab API calls
# Remove: Complex lab result processing
```

## PHASE B: ARCHITECTURAL FIXES (60 minutes)

### 1. Standardize ALL API Calls
```bash
# Replace in App.js (77 occurrences):
axios.get(`${API}/endpoint`) → api.get('/endpoint')
axios.post(`${API}/endpoint`) → api.post('/endpoint')
# etc.
```

### 2. Clean Environment Variables
```bash
# Remove duplicate definitions:
const BACKEND_URL = ...
const API = ...

# Use only configured api instance
```

### 3. Fix Authentication Flow
```bash
# Ensure all components use contexts/AuthContext
# Remove duplicate auth implementations
```

## PHASE C: TESTING & VALIDATION (30 minutes)

### 1. Test Core EHR Functions
- Patient management
- Appointments  
- SOAP notes
- Basic reporting

### 2. Test Authentication
- Login/logout
- JWT token handling
- Protected routes

### 3. Test API Consistency
- All endpoints use /api prefix
- No double API paths
- Consistent error handling