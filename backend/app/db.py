import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI environment variable not set")

DB_NAME = os.getenv("MONGODB_DB", "guardian_health")

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def get_db():
    return db

async def get_user_collection():
    return db["users"]

async def get_chats_collection():
    return db["chats"]

async def get_interactions_collection():
    return db["interactions"]
