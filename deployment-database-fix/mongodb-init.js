// MongoDB Initialization Script for ClinicHub Deployment
// This script must be executed on the new internal MongoDB instance

print('🏥 ClinicHub MongoDB Deployment Initialization Starting...');

// Switch to the clinichub database
db = db.getSiblingDB('clinichub');

// Create application user with strong password
db.createUser({
  user: 'clinichub_user',
  pwd: 'ClinicHub2025#MongoDB!Secure',
  roles: [
    {
      role: 'readWrite',
      db: 'clinichub'
    },
    {
      role: 'dbAdmin',
      db: 'clinichub'
    }
  ]
});

print('✅ Created clinichub_user with readWrite and dbAdmin roles');

// Create essential collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['id', 'username', 'email', 'role'],
      properties: {
        id: { bsonType: 'string' },
        username: { bsonType: 'string' },
        email: { bsonType: 'string' },
        role: { enum: ['admin', 'doctor', 'nurse', 'staff', 'billing'] },
        is_active: { bsonType: 'bool' }
      }
    }
  }
});

db.createCollection('patients', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['id', 'first_name', 'last_name'],
      properties: {
        id: { bsonType: 'string' },
        first_name: { bsonType: 'string' },
        last_name: { bsonType: 'string' },
        date_of_birth: { bsonType: 'string' },
        email: { bsonType: 'string' },
        phone: { bsonType: 'string' }
      }
    }
  }
});

db.createCollection('encounters', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['id', 'patient_id', 'provider_id', 'date'],
      properties: {
        id: { bsonType: 'string' },
        patient_id: { bsonType: 'string' },
        provider_id: { bsonType: 'string' },
        date: { bsonType: 'string' },
        type: { bsonType: 'string' }
      }
    }
  }
});

print('✅ Created core collections with validation schemas');

// Create performance indexes
db.users.createIndex({ 'username': 1 }, { unique: true });
db.users.createIndex({ 'email': 1 }, { unique: true });
db.users.createIndex({ 'id': 1 }, { unique: true });
db.users.createIndex({ 'role': 1 });

db.patients.createIndex({ 'id': 1 }, { unique: true });
db.patients.createIndex({ 'first_name': 1, 'last_name': 1 });
db.patients.createIndex({ 'date_of_birth': 1 });
db.patients.createIndex({ 'email': 1 });

db.encounters.createIndex({ 'patient_id': 1 });
db.encounters.createIndex({ 'provider_id': 1 });
db.encounters.createIndex({ 'date': -1 });
db.encounters.createIndex({ 'id': 1 }, { unique: true });

db.appointments.createIndex({ 'patient_id': 1 });
db.appointments.createIndex({ 'provider_id': 1 });
db.appointments.createIndex({ 'start_time': 1 });
db.appointments.createIndex({ 'id': 1 }, { unique: true });

print('✅ Created performance indexes on all collections');

// Insert default admin user (same as existing system)
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
  updated_at: new Date(),
  settings: {
    theme: 'light',
    notifications: true,
    two_factor_enabled: false
  }
});

print('✅ Created default admin user: admin/admin123');

// Create system configuration collection
db.system_config.insertOne({
  id: 'clinic-config-001',
  clinic_name: 'ClinicHub Medical Practice',
  version: '1.0.0',
  deployment_environment: 'production',
  database_initialized: new Date(),
  features_enabled: {
    telehealth: true,
    billing: true,
    inventory: true,
    payroll: true,
    erx: true,
    audit_logging: true
  }
});

print('✅ System configuration initialized');

print('🎉 ClinicHub MongoDB initialization completed successfully!');
print('📋 Summary:');
print('   - Database: clinichub');
print('   - User: clinichub_user');
print('   - Collections: users, patients, encounters, appointments');
print('   - Admin credentials: admin/admin123');
print('   - Status: Ready for production deployment');