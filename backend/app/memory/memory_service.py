"""VeriMind AI - Memory Service."""
from __future__ import annotations
from typing import Any
from uuid import uuid4
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

class MemoryService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_short_term(self, user_id: str) -> list[dict]:
        cursor = self.db.memory.find(
            {"user_id": user_id, "type": "short_term"}
        ).sort("created_at", -1).limit(10)
        docs = await cursor.to_list(length=10)
        return [m.get("content", {}) for m in docs]

    async def get_long_term(self, user_id: str) -> list[dict]:
        cursor = self.db.memory.find(
            {"user_id": user_id, "type": "long_term"}
        ).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [m.get("content", {}) for m in docs]

    async def get_requirement_memory(self, user_id: str) -> list[dict]:
        cursor = self.db.memory.find(
            {"user_id": user_id, "type": "requirement"}
        ).sort("created_at", -1)
        docs = await cursor.to_list(length=None)
        return [m.get("content", {}) for m in docs]

    async def save_memory(
        self, user_id: str, memory_type: str, content: dict
    ) -> dict[str, Any]:
        mem = {
            "_id": str(uuid4()),
            "user_id": user_id,
            "type": memory_type,
            "content": content,
            "created_at": datetime.utcnow()
        }
        await self.db.memory.insert_one(mem)
        mem["id"] = mem.pop("_id")
        return mem
