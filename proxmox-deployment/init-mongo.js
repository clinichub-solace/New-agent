// MongoDB initialization script for ClinicHub
print('Starting ClinicHub MongoDB initialization...');

// Switch to the clinichub database
db = db.getSiblingDB('clinichub');

// Create application user
db.createUser({
  user: 'clinichub_app',
  pwd: 'clinichub_app_password_change_me',
  roles: [
    {
      role: 'readWrite',
      db: 'clinichub'
    }
  ]
});

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['id', 'username', 'email', 'role'],
      properties: {
        id: { bsonType: 'string' },
        username: { bsonType: 'string' },
        email: { bsonType: 'string' },
        role: { enum: ['admin', 'doctor', 'nurse', 'staff'] }
      }
    }
  }
});

db.createCollection('patients', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['id', 'first_name', 'last_name', 'date_of_birth'],
      properties: {
        id: { bsonType: 'string' },
        first_name: { bsonType: 'string' },
        last_name: { bsonType: 'string' },
        date_of_birth: { bsonType: 'string' }
      }
    }
  }
});

// Create indexes for performance
db.users.createIndex({ 'username': 1 }, { unique: true });
db.users.createIndex({ 'email': 1 }, { unique: true });
db.users.createIndex({ 'id': 1 }, { unique: true });

db.patients.createIndex({ 'id': 1 }, { unique: true });
db.patients.createIndex({ 'first_name': 1, 'last_name': 1 });
db.patients.createIndex({ 'date_of_birth': 1 });

db.encounters.createIndex({ 'patient_id': 1 });
db.encounters.createIndex({ 'date': -1 });

db.appointments.createIndex({ 'patient_id': 1 });
db.appointments.createIndex({ 'provider_id': 1 });
db.appointments.createIndex({ 'start_time': 1 });

// Insert default admin user
db.users.insertOne({
  id: 'admin-user-001',
  username: 'admin',
  email: 'admin@clinichub.local',
  password_hash: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPa0MuFMGPGHO', // admin123
  role: 'admin',
  is_active: true,
  first_name: 'System',
  last_name: 'Administrator',
  created_at: new Date(),
  updated_at: new Date()
});

print('ClinicHub MongoDB initialization completed successfully!');
print('Default admin user: admin / admin123');