// ClinicHub MongoDB Initialization Script
// Run this script to set up the database with initial data

// Switch to clinichub database
use clinichub;

// Create admin user
db.users.insertOne({
    "id": "admin",
    "username": "admin",
    "email": "admin@clinichub.com",
    "first_name": "System",
    "last_name": "Administrator", 
    "role": "admin",
    "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LQ1u/OfJb9qW9W4X8J8.dX0GJ.uOtGjY4Q0Eq", // admin123
    "is_active": true,
    "created_at": new Date().toISOString(),
    "permissions": ["*"]
});

// Create sample patient data for demo
db.patients.insertMany([
    {
        "id": "patient-001",
        "resourceType": "Patient",
        "name": [{
            "given": ["John"],
            "family": "Doe"
        }],
        "gender": "male",
        "birthDate": "1985-03-15",
        "telecom": [
            {"system": "phone", "value": "555-0123"},
            {"system": "email", "value": "john.doe@email.com"}
        ],
        "address": [{
            "line": ["123 Main Street"],
            "city": "Austin",
            "state": "TX",
            "postalCode": "78701",
            "country": "USA"
        }],
        "created_at": new Date().toISOString()
    },
    {
        "id": "patient-002", 
        "resourceType": "Patient",
        "name": [{
            "given": ["Jane"],
            "family": "Smith"
        }],
        "gender": "female",
        "birthDate": "1990-07-22",
        "telecom": [
            {"system": "phone", "value": "555-0456"},
            {"system": "email", "value": "jane.smith@email.com"}
        ],
        "address": [{
            "line": ["456 Oak Avenue"],
            "city": "Dallas", 
            "state": "TX",
            "postalCode": "75201",
            "country": "USA"
        }],
        "created_at": new Date().toISOString()
    }
]);

// Create sample employees
db.employees.insertMany([
    {
        "id": "emp-001",
        "employee_id": "EMP-001",
        "first_name": "Dr. Sarah",
        "last_name": "Johnson",
        "email": "sarah.johnson@clinichub.com",
        "role": "doctor",
        "department": "Internal Medicine",
        "hire_date": "2024-01-15",
        "hourly_rate": 75.00,
        "salary": 150000.00,
        "is_active": true,
        "created_at": new Date().toISOString()
    },
    {
        "id": "emp-002",
        "employee_id": "EMP-002", 
        "first_name": "Lisa",
        "last_name": "Chen",
        "email": "lisa.chen@clinichub.com",
        "role": "nurse",
        "department": "General",
        "hire_date": "2024-02-01",
        "hourly_rate": 35.00,
        "is_active": true,
        "created_at": new Date().toISOString()
    }
]);

// Create sample inventory items
db.inventory.insertMany([
    {
        "id": "inv-001",
        "item_name": "Digital Thermometer",
        "category": "Medical Equipment",
        "current_stock": 25,
        "min_stock_level": 5,
        "max_stock_level": 50,
        "unit_cost": 29.99,
        "supplier": "MedSupply Inc",
        "location": "Storage Room A",
        "expiry_date": "2026-12-31",
        "created_at": new Date().toISOString()
    },
    {
        "id": "inv-002",
        "item_name": "Disposable Gloves (Box)",
        "category": "Medical Supplies",
        "current_stock": 15,
        "min_stock_level": 10,
        "max_stock_level": 100,
        "unit_cost": 12.50,
        "supplier": "HealthCare Supplies Co",
        "location": "Supply Closet",
        "expiry_date": "2025-06-30",
        "created_at": new Date().toISOString()
    }
]);

// Create ICD-10 sample codes
db.icd10_codes.insertMany([
    {
        "id": "icd-001",
        "code": "E11.9",
        "description": "Type 2 diabetes mellitus without complications",
        "category": "Endocrine",
        "search_terms": ["diabetes", "type 2", "dm", "blood sugar", "glucose"]
    },
    {
        "id": "icd-002",
        "code": "I10",
        "description": "Essential hypertension", 
        "category": "Cardiovascular",
        "search_terms": ["hypertension", "high blood pressure", "htn", "bp"]
    },
    {
        "id": "icd-003",
        "code": "Z00.00",
        "description": "Encounter for general adult medical examination without abnormal findings",
        "category": "Preventive Care",
        "search_terms": ["physical", "checkup", "annual", "exam", "wellness"]
    }
]);

// Create indexes for performance
db.users.createIndex({"username": 1}, {unique: true});
db.patients.createIndex({"id": 1}, {unique: true});
db.employees.createIndex({"employee_id": 1}, {unique: true});
db.inventory.createIndex({"item_name": 1});
db.icd10_codes.createIndex({"code": 1}, {unique: true});
db.icd10_codes.createIndex({"search_terms": 1});

// Create notification collection
db.notifications.createIndex({"recipient_id": 1, "created_at": -1});
db.notifications.createIndex({"acknowledged": 1});

// Create audit log collection  
db.audit_log.createIndex({"timestamp": -1});
db.audit_log.createIndex({"resource_type": 1, "timestamp": -1});
db.audit_log.createIndex({"user_id": 1, "timestamp": -1});

print("✅ ClinicHub database initialized successfully");
print("📊 Created sample data for demo");
print("🔐 Default login: admin / admin123");