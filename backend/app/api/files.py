"""VeriMind AI - Files API Endpoints."""
from __future__ import annotations
from uuid import uuid4
import os
import aiofiles
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.database.connection import get_db
from app.config import get_settings
from app.services.document_service import process_document

router = APIRouter(prefix="/api/files", tags=["files"])
settings = get_settings()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    allowed_types = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "text/plain": "txt",
        "text/csv": "csv",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
        "image/png": "image",
        "image/jpeg": "image",
    }
    file_type = allowed_types.get(file.content_type)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Supported: PDF, DOCX, TXT, CSV, PPTX, PNG, JPEG",
        )

    content = await file.read()
    file_size = len(content)
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    upload_dir = os.path.join(settings.UPLOAD_DIR, "documents")
    os.makedirs(upload_dir, exist_ok=True)
    doc_id = str(uuid4())
    file_path = os.path.join(upload_dir, f"{doc_id}_{file.filename}")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    doc: dict[str, Any] = {
        "_id": doc_id,
        "filename": file.filename,
        "file_type": file_type,
        "file_size": file_size,
        "storage_path": file_path,
        "conversation_id": conversation_id,
        "status": "processing",
        "page_count": 0,
        "created_at": datetime.utcnow(),
    }
    await db.documents.insert_one(doc)

    try:
        page_count = await process_document(db, doc_id, doc, content)
        await db.documents.update_one(
            {"_id": doc_id},
            {"$set": {"status": "processed", "page_count": page_count}}
        )
        doc["status"] = "processed"
        doc["page_count"] = page_count
    except Exception as e:
        await db.documents.update_one(
            {"_id": doc_id},
            {"$set": {"status": "failed"}}
        )
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

    doc["id"] = doc.pop("_id")
    return doc

@router.get("/documents")
async def list_documents(
    conversation_id: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {}
    if conversation_id:
        query["conversation_id"] = conversation_id
    cursor = db.documents.find(query).sort("created_at", -1)
    documents = await cursor.to_list(length=None)
    for doc in documents:
        doc["id"] = doc.pop("_id")
    return documents

@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: str,
    section: str = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    query = {"document_id": document_id}
    if section:
        query["section_name"] = section
    cursor = db.document_chunks.find(query).sort("page_number", 1)
    chunks = await cursor.to_list(length=None)
    return [
        {
            "id": c["_id"],
            "page_number": c.get("page_number"),
            "section_name": c.get("section_name"),
            "content": c.get("content", "")[:500],
        }
        for c in chunks
    ]
