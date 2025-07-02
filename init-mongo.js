/* eslint-disable */
// MongoDB initialization script
db = db.getSiblingDB('clinichub');

// Create initial admin user
db.users.insertOne({
    username: "admin",
    email: "admin@clinichub.com", 
    password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6QOGhk6jHW", // admin123
    role: "admin",
    permissions: ["*"],
    created_at: new Date(),
    is_active: true
});

// Create indexes for better performance
db.patients.createIndex({ "email": 1 }, { unique: true });
db.patients.createIndex({ "name.family": 1, "name.given": 1 });
db.appointments.createIndex({ "date": 1, "time": 1 });
db.appointments.createIndex({ "patient_id": 1 });
db.encounters.createIndex({ "patient_id": 1, "date": -1 });
db.lab_orders.createIndex({ "patient_id": 1, "created_at": -1 });
db.invoices.createIndex({ "patient_id": 1, "status": 1 });

print("ClinicHub database initialized successfully!");