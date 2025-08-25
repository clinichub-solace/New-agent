# ClinicHub Dependencies - Clean Version for Deployment
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Simple MongoDB connection for deployment
def get_mongo_client():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/clinichub')
    return AsyncIOMotorClient(mongo_url)

# Database instance
client = get_mongo_client()
db = client[os.environ.get('DB_NAME', 'clinichub')]