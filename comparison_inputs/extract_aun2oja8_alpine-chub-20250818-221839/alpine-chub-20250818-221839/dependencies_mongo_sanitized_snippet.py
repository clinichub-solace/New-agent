# --- DROP-IN SNIPPET for backend/dependencies.py (Mongo client init) ---
from urllib.parse import urlparse, quote
from motor.motor_asyncio import AsyncIOMotorClient
import os

mongo_url = read_secret('mongo_connection_string', 'MONGO_URL')
if not mongo_url:
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/clinichub')

def sanitize_mongo_uri(uri: str) -> str:
    p = urlparse(uri)
    if not (p.username or p.password):
        return uri  # nothing to encode
    user = quote(p.username or '', safe='')
    pw   = quote(p.password or '', safe='')
    query = f'?{p.query}' if p.query else ''
    path  = p.path or '/clinichub'
    host  = p.hostname or 'localhost'
    port  = f":{p.port}" if p.port else ''
    return f"mongodb://{user}:{pw}@{host}{port}{path}{query}"

mongo_url = sanitize_mongo_uri(mongo_url)
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'clinichub')]
# --- END SNIPPET ---
