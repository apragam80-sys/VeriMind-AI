"""VeriMind AI - History API Endpoints."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from app.database.connection import get_db
from app.models.schemas import ConversationUpdate

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("/conversations")
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.conversations.find(
        {"is_archived": False}
    ).sort("updated_at", -1).skip(offset).limit(limit)
    conversations = await cursor.to_list(length=limit)
    for conv in conversations:
        conv["id"] = conv.pop("_id")
    return conversations

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    conv = await db.conversations.find_one({"_id": conversation_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv["id"] = conv.pop("_id")
    return conv

@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    update_data: dict[str, Any] = {"updated_at": datetime.utcnow()}
    if data.title is not None:
        update_data["title"] = data.title
    if data.is_archived is not None:
        update_data["is_archived"] = data.is_archived

    result = await db.conversations.update_one(
        {"_id": conversation_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = await db.conversations.find_one({"_id": conversation_id})
    conv["id"] = conv.pop("_id")
    return conv

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db.conversations.delete_one({"_id": conversation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.messages.delete_many({"conversation_id": conversation_id})
    await db.requirement_lock.delete_one({"conversation_id": conversation_id})
    return {"status": "deleted"}

@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    cursor = db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("created_at", 1)
    messages = await cursor.to_list(length=None)
    for msg in messages:
        msg["id"] = msg.pop("_id")
    return messages
