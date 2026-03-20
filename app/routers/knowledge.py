"""Knowledge router – upload documents to build the knowledge base."""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import tempfile

from fastapi import APIRouter, File, UploadFile

from app.knowledge.parser import parse_document
from app.knowledge.processor import process_document
from app.knowledge.vectorstore import add_documents
from app.models.schemas import DocumentUploadResponse
from app.rag.llm import get_embeddings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    device_type: str = "",
):
    """Upload a device manual / document and ingest it into the vector store."""
    # Save to temp file
    suffix = os.path.splitext(file.filename or "doc")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        raw_text = parse_document(tmp_path)
        chunks = process_document(raw_text)

        # Build ids and metadata
        ids: list[str] = []
        metadatas: list[dict] = []
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(f"{file.filename}:{i}:{chunk[:64]}".encode()).hexdigest()[:16]
            ids.append(chunk_id)
            meta = {"filename": file.filename, "chunk_index": i}
            if device_type:
                meta["device_type"] = device_type
            metadatas.append(meta)

        # Compute embeddings
        embeddings = get_embeddings(chunks)

        # Store
        add_documents(texts=chunks, metadatas=metadatas, ids=ids, embeddings=embeddings)

        return DocumentUploadResponse(filename=file.filename or "", chunk_count=len(chunks))
    finally:
        os.unlink(tmp_path)
