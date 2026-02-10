from __future__ import annotations
import hashlib
from typing import Dict, List, Tuple, Any


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def dedupe_exact(records: List[Dict[str, Any]], hash_field: str = "exact_hash") -> Tuple[List[Dict[str, Any]], int]:
    """
    Keep first occurrence for each exact hash. Returns (kept, removed_count).
    """
    seen = set()
    kept = []
    removed = 0
    for r in records:
        h = r.get(hash_field)
        if not h:
            kept.append(r)
            continue
        if h in seen:
            removed += 1
            continue
        seen.add(h)
        kept.append(r)
    return kept, removed
