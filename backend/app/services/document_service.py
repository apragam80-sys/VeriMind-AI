"""VeriMind AI - Document Processing Service."""
from __future__ import annotations
from typing import Any
import re
from uuid import uuid4

SECTION_PATTERNS = [
    r"(?i)^(?:\d+\.?\s*)?abstract",
    r"(?i)^(?:\d+\.?\s*)?introduction",
    r"(?i)^(?:\d+\.?\s*)?related\s+work",
    r"(?i)^(?:\d+\.?\s*)?background",
    r"(?i)^(?:\d+\.?\s*)?methodology",
    r"(?i)^(?:\d+\.?\s*)?method(?:s)?",
    r"(?i)^(?:\d+\.?\s*)?proposed\s+(?:method|approach|system|framework)",
    r"(?i)^(?:\d+\.?\s*)?experiment(?:s|al)?(?:\s+(?:setup|results))?",
    r"(?i)^(?:\d+\.?\s*)?results?(?:\s+and\s+discussion)?",
    r"(?i)^(?:\d+\.?\s*)?discussion",
    r"(?i)^(?:\d+\.?\s*)?evaluation",
    r"(?i)^(?:\d+\.?\s*)?analysis",
    r"(?i)^(?:\d+\.?\s*)?implementation",
    r"(?i)^(?:\d+\.?\s*)?conclusion(?:s)?",
    r"(?i)^(?:\d+\.?\s*)?future\s+work",
    r"(?i)^(?:\d+\.?\s*)?references",
    r"(?i)^(?:\d+\.?\s*)?appendix",
    r"(?i)^(?:\d+\.?\s*)?acknowledgment(?:s)?",
]

def detect_section(line: str) -> str | None:
    stripped = line.strip()
    if len(stripped) < 3 or len(stripped) > 100:
        return None
    for pattern in SECTION_PATTERNS:
        if re.match(pattern, stripped):
            name = re.sub(r"^\d+\.?\s*", "", stripped).strip()
            return name.title()
    return None

def structure_aware_chunk(
    text: str,
    max_chunk_size: int = 1500,
) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_section = "Introduction"
    current_content: list[str] = []
    current_page = 1

    lines = text.split("\n")
    for line in lines:
        section = detect_section(line)
        if section:
            if current_content:
                content = "\n".join(current_content).strip()
                if content:
                    if len(content) > max_chunk_size:
                        for i in range(0, len(content), max_chunk_size):
                            chunks.append({
                                "section_name": current_section,
                                "content": content[i:i + max_chunk_size],
                                "page_number": current_page,
                            })
                    else:
                        chunks.append({
                            "section_name": current_section,
                            "content": content,
                            "page_number": current_page,
                        })
            current_section = section
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        content = "\n".join(current_content).strip()
        if content:
            if len(content) > max_chunk_size:
                for i in range(0, len(content), max_chunk_size):
                    chunks.append({
                        "section_name": current_section,
                        "content": content[i:i + max_chunk_size],
                        "page_number": current_page,
                    })
            else:
                chunks.append({
                    "section_name": current_section,
                    "content": content,
                    "page_number": current_page,
                })
    return chunks

def extract_text_from_pdf(content: bytes) -> tuple[str, int]:
    import io
    from pypdf import PdfReader
    
    reader = PdfReader(io.BytesIO(content))
    full_text = ""
    for page_num, page in enumerate(reader.pages, 1):
        text = page.extract_text()
        if text:
            full_text += f"\n--- Page {page_num} ---\n{text}"
    page_count = len(reader.pages)
    return full_text, page_count

def extract_text_from_docx(content: bytes) -> tuple[str, int]:
    import io
    from docx import Document as DocxDocument
    doc = DocxDocument(io.BytesIO(content))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n".join(paragraphs)
    page_count = max(1, len(full_text) // 3000)
    return full_text, page_count

def extract_text_plain(content: bytes) -> tuple[str, int]:
    text = content.decode("utf-8", errors="ignore")
    page_count = max(1, len(text) // 3000)
    return text, page_count

async def process_document(
    db: Any,
    document_id: str,
    document: dict[str, Any],
    content: bytes,
) -> int:
    extractors = {
        "pdf": extract_text_from_pdf,
        "docx": extract_text_from_docx,
        "txt": extract_text_plain,
        "csv": extract_text_plain,
    }
    extractor = extractors.get(document.get("file_type"))
    if not extractor:
        raise ValueError(f"Unsupported file type: {document.get('file_type')}")

    full_text, page_count = extractor(content)
    chunks = structure_aware_chunk(full_text)

    if chunks:
        chunk_docs = [
            {
                "_id": str(uuid4()),
                "document_id": document_id,
                "page_number": chunk_data["page_number"],
                "section_name": chunk_data["section_name"],
                "content": chunk_data["content"],
            }
            for chunk_data in chunks
        ]
        await db.document_chunks.insert_many(chunk_docs)

    return page_count
