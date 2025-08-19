use clinichub;

db.createUser({
  user: "admin",
  pwd: "ClinicHub2024!Secure",
  roles: [
    { role: "readWrite", db: "clinichub" },
    { role: "dbAdmin", db: "clinichub" }
  ]
});

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

print("ClinicHub database initialized with sample data!");
