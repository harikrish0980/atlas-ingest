from __future__ import annotations
from typing import List


def chunk_words(text: str, chunk_size: int = 350, overlap: int = 50) -> List[str]:
    """
    Word-based chunking with overlap. Simple, reliable, and good for demos.
    """
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    i = 0
    while i < len(words):
        j = min(len(words), i + chunk_size)
        chunks.append(" ".join(words[i:j]))
        if j >= len(words):
            break
        i = max(0, j - overlap)

    return chunks
