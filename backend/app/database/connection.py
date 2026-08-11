"""VeriMind AI - Database Connection (MongoDB)."""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

settings = get_settings()

import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_manager = DatabaseManager()

async def connect_db():
    MONGODB_URL = os.getenv("MONGODB_URL", settings.MONGODB_URL)
    MONGODB_NAME = os.getenv("MONGODB_NAME", settings.MONGODB_NAME)
    
    db_manager.client = AsyncIOMotorClient(MONGODB_URL)
    db_manager.db = db_manager.client[MONGODB_NAME]
    
    # Create indexes
    await db_manager.db.conversations.create_index("updated_at")
    await db_manager.db.messages.create_index("conversation_id")
    await db_manager.db.documents.create_index("conversation_id")
    await db_manager.db.document_chunks.create_index("document_id")
    await db_manager.db.memory.create_index("user_id")

async def close_db():
    if db_manager.client:
        db_manager.client.close()

def get_db() -> AsyncIOMotorDatabase:
    return db_manager.db
