"""Text processor – cleaning, segmentation and chunking."""

from __future__ import annotations

import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def clean_text(text: str) -> str:
    """Basic text cleaning: collapse whitespace, strip control chars."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def split_text(text: str) -> list[str]:
    """Split cleaned text into chunks suitable for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n\n", "\n", "。", ".", "！", "!", "？", "?", " "],
    )
    return splitter.split_text(text)


def process_document(text: str) -> list[str]:
    """Clean then split a raw document text into chunks."""
    return split_text(clean_text(text))
