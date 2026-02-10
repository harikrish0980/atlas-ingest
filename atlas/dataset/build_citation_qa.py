# atlas/dataset/build_citation_qa.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from atlas.store.jsonl_writer import read_jsonl, write_jsonl


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _first_sentences(text: str, n: int = 2) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    parts = _SENT_SPLIT.split(text)
    parts = [p.strip() for p in parts if p.strip()]
    return " ".join(parts[:n])


def _make_question(text: str) -> str:
    """
    Heuristic question generator:
    - If first sentence starts with a noun phrase, ask 'What does it say about ...?'
    - Else generic.
    """
    s1 = _first_sentences(text, n=1)
    if not s1:
        return "What does the passage describe?"
    # If it's long, use first ~8 words as topic
    words = s1.split()
    topic = " ".join(words[:8]).rstrip(",:;")
    return f"What does the passage say about: {topic}?"


def build_citation_qa_dataset(
    chunks_jsonl: Path,
    out_jsonl: Path,
    max_rows: int = 300,
    min_chars: int = 200,
) -> Dict[str, Any]:
    rows = read_jsonl(chunks_jsonl)

    out: List[Dict[str, Any]] = []
    kept = 0
    skipped_short = 0

    for r in rows:
        if kept >= max_rows:
            break
        text = (r.get("text") or "").strip()
        if len(text) < min_chars:
            skipped_short += 1
            continue

        question = _make_question(text)
        answer = _first_sentences(text, n=2)
        citation = f"{r.get('source_uri')}#chunk={r.get('chunk_id')}"

        example = {
            "id": r.get("chunk_id"),
            "prompt": (
                "You are given a context passage. "
                "Write a short answer to the question using only the context. "
                "Include a citation in the form [source].\n\n"
                f"Question: {question}\n\n"
                "Context:\n"
                f"{text}\n\n"
                "Answer:"
            ),
            "context": text,
            "question": question,
            "answer": f"{answer} [{citation}]",
            "citation": citation,
            "source_uri": r.get("source_uri"),
            "doc_id": r.get("doc_id"),
        }
        out.append(example)
        kept += 1

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_jsonl, out)

    return {
        "written": kept,
        "skipped_short": skipped_short,
        "out": str(out_jsonl),
    }
