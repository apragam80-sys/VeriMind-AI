"""VeriMind AI - Pydantic Schemas."""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ConversationOut(BaseModel):
    id: str
    title: str
    is_archived: bool
    created_at: str
    updated_at: str

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None

class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    response_mode: Optional[str] = None
    created_at: str

class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    page_count: int
    created_at: str
