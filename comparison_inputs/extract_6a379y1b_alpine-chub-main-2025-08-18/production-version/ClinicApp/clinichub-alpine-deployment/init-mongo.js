// MongoDB initialization script for ClinicHub
use clinichub;

// Create admin user
db.createUser({
  user: "admin",
  pwd: "ClinicHub2024!Secure",
  roles: [
    { role: "readWrite", db: "clinichub" },
    { role: "dbAdmin", db: "clinichub" }
  ]
});

// Create indexes for better performance
db.patients.createIndex({ "email": 1 }, { unique: true });
db.patients.createIndex({ "mrn": 1 }, { unique: true });
db.employees.createIndex({ "employee_id": 1 }, { unique: true });
db.appointments.createIndex({ "patient_id": 1 });
db.appointments.createIndex({ "provider_id": 1 });
db.appointments.createIndex({ "scheduled_date": 1 });

// Initialize sample data
db.patients.insertMany([
  {
    "id": "pat_001",
    "mrn": "MRN001001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@email.com",
    "phone": "555-0101",
    "date_of_birth": "1985-05-15",
    "gender": "Male",
    "created_at": new Date()
  },
  {
    "id": "pat_002",
    "mrn": "MRN001002",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@email.com",
    "phone": "555-0102",
    "date_of_birth": "1990-08-22",
    "gender": "Female",
    "created_at": new Date()
  }
]);

db.employees.insertMany([
  {
    "employee_id": "emp_001",
    "first_name": "Dr. Sarah",
    "last_name": "Johnson",
    "role": "Physician",
    "specialty": "Internal Medicine",
    "email": "sarah.johnson@clinic.com",
    "created_at": new Date()
  },
  {
    "employee_id": "emp_002",
    "first_name": "Dr. Michael",
    "last_name": "Brown",
    "role": "Physician",
    "specialty": "Cardiology",
    "email": "michael.brown@clinic.com",
    "created_at": new Date()
  }
]);

print("ClinicHub database initialized successfully with sample data!");