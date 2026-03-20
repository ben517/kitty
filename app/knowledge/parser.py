"""Document parser – extracts text from PDF, Word and HTML files."""

from __future__ import annotations

import os
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredHTMLLoader,
)


def _load_docx(file_path: str) -> str:
    import docx2txt

    return docx2txt.process(file_path)


def parse_document(file_path: str) -> str:
    """Return raw text extracted from a single document file."""
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        return "\n".join(p.page_content for p in pages)

    if ext in (".docx", ".doc"):
        return _load_docx(file_path)

    if ext in (".html", ".htm"):
        loader = UnstructuredHTMLLoader(file_path)
        docs = loader.load()
        return "\n".join(d.page_content for d in docs)

    if ext in (".txt", ".md"):
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
        return "\n".join(d.page_content for d in docs)

    raise ValueError(f"Unsupported file type: {ext}")


def parse_directory(dir_path: str) -> list[dict]:
    """Parse all supported documents in *dir_path*.

    Returns a list of ``{"filename": ..., "content": ...}`` dicts.
    """
    supported = {".pdf", ".docx", ".doc", ".html", ".htm", ".txt", ".md"}
    results: list[dict] = []
    for root, _, files in os.walk(dir_path):
        for fname in files:
            if Path(fname).suffix.lower() in supported:
                fpath = os.path.join(root, fname)
                text = parse_document(fpath)
                results.append({"filename": fname, "content": text})
    return results
