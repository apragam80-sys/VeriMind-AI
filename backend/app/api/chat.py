"""VeriMind AI - Chat API Endpoints.

Handles chat messages via SSE streaming and REST endpoints.
All AI logic is delegated to the AI Orchestrator.
Uses MongoDB (Motor) for persistence.
"""
from __future__ import annotations
from uuid import uuid4
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.connection import get_db
from app.models.schemas import ChatRequest
from app.orchestrator.ai_orchestrator import get_orchestrator

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("")
async def send_message(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    orchestrator = get_orchestrator()
    now = datetime.utcnow()

    conversation_id = str(request.conversation_id) if request.conversation_id else str(uuid4())
    
    conv = await db.conversations.find_one({"_id": conversation_id})
    if not conv:
        await db.conversations.insert_one({
            "_id": conversation_id,
            "title": request.message[:100],
            "created_at": now,
            "updated_at": now,
            "is_archived": False,
        })
    else:
        await db.conversations.update_one(
            {"_id": conversation_id},
            {"$set": {"updated_at": now}}
        )

    user_msg_id = str(uuid4())
    await db.messages.insert_one({
        "_id": user_msg_id,
        "conversation_id": conversation_id,
        "role": "user",
        "content": request.message,
        "created_at": now,
    })

    cursor = db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("created_at", -1).limit(20)
    history_docs = await cursor.to_list(length=20)
    history = [
        {"role": doc["role"], "content": doc["content"]}
        for doc in reversed(history_docs)
    ]

    pipeline_result = await orchestrator.process_query(
        user_message=request.message,
        conversation_id=conversation_id,
        conversation_history=history,
    )

    ai_msg_id = str(uuid4())
    await db.messages.insert_one({
        "_id": ai_msg_id,
        "conversation_id": conversation_id,
        "role": "assistant",
        "content": pipeline_result["response"],
        "response_mode": pipeline_result.get("response_mode", "verified"),
        "created_at": datetime.utcnow(),
    })

    confidence = pipeline_result.get("confidence", {})
    if confidence:
        await db.verification_logs.insert_one({
            "_id": str(uuid4()),
            "message_id": ai_msg_id,
            "confidence_score": confidence.get("requirement_match", 0),
            "evidence_support": confidence.get("evidence_support", 0),
            "requirement_match": confidence.get("requirement_match", 0),
            "hallucination_risk": confidence.get("hallucination_risk", 0),
            "approved": True,
            "created_at": datetime.utcnow(),
        })

    evidence_list = pipeline_result.get("evidence_ledger", [])
    if evidence_list:
        evidence_docs = [
            {
                "_id": str(uuid4()),
                "message_id": ai_msg_id,
                "claim": claim.get("claim", ""),
                "source": claim.get("source"),
                "page": claim.get("page"),
                "section": claim.get("section"),
                "confidence": claim.get("confidence", 0),
                "created_at": datetime.utcnow(),
            }
            for claim in evidence_list
        ]
        await db.evidence_ledger.insert_many(evidence_docs)

    req_lock = pipeline_result.get("requirement_lock")
    if req_lock:
        await db.requirement_lock.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "allowed_topics": req_lock.get("allowed_topics", []),
                    "forbidden_topics": req_lock.get("forbidden_topics", []),
                    "assumptions_allowed": req_lock.get("assumptions_allowed", []),
                    "assumptions_forbidden": req_lock.get("assumptions_forbidden", []),
                    "confidence": req_lock.get("confidence", 0),
                    "updated_at": datetime.utcnow(),
                },
                "$setOnInsert": {
                    "_id": str(uuid4()),
                    "created_at": datetime.utcnow(),
                }
            },
            upsert=True
        )

    return {
        "conversation_id": conversation_id,
        "message_id": ai_msg_id,
        "content": pipeline_result["response"],
        "response_mode": pipeline_result.get("response_mode", "verified"),
        "confidence": confidence,
        "evidence": pipeline_result.get("evidence_ledger", []),
        "requirement_lock": req_lock,
        "intent": pipeline_result.get("intent"),
        "plan": pipeline_result.get("plan"),
    }

@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    orchestrator = get_orchestrator()

    history = []
    if request.conversation_id:
        conversation_id = str(request.conversation_id)
        cursor = db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", -1).limit(20)
        history_docs = await cursor.to_list(length=20)
        history = [
            {"role": doc["role"], "content": doc["content"]}
            for doc in reversed(history_docs)
        ]

    async def event_generator():
        async for event in orchestrator.process_query_stream(
            user_message=request.message,
            conversation_id=str(request.conversation_id) if request.conversation_id else None,
            conversation_history=history,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
