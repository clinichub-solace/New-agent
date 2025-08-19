#!/usr/bin/env python3
"""
Setup test user for payroll smoke testing
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def setup_test_user():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://admin:changeme123@mongodb:27017/clinichub?authSource=admin')
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'clinichub')]
    
    # Create test user
    test_user = {
        "id": str(uuid.uuid4()),
        "username": "testuser",
        "password": pwd_context.hash("testpass"),
        "email": "test@test.com", 
        "first_name": "Test",
        "last_name": "User",
        "role": "admin",
        "permissions": ["*"],
        "is_active": True,
        "auth_source": "local",
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    # Upsert the user
    await db.users.update_one(
        {"username": "testuser"},
        {"$set": test_user},
        upsert=True
    )
    
    print("✅ Test user created successfully")
    print("Username: testuser")
    print("Password: testpass")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(setup_test_user())