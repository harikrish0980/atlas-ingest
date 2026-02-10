from __future__ import annotations
import re


def normalize_text(text: str) -> str:
    """
    Clean/normalize text for chunking and indexing.
    """
    if not text:
        return ""
    t = text.replace("\r", "\n")

    # Fix hyphenated line breaks: "inter-\nnet" -> "internet"
    t = re.sub(r"(\w)-\n(\w)", r"\1\2", t)

    # Normalize whitespace
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n[ \t]+", "\n", t)

    # Collapse excessive blank lines
    t = re.sub(r"\n{3,}", "\n\n", t)

    # Remove control chars (except newline/tab)
    t = "".join(ch for ch in t if ch == "\n" or ch == "\t" or (ord(ch) >= 32 and ord(ch) != 127))

    return t.strip()


def gibberish_score(text: str) -> float:
    """
    Simple extraction-quality heuristic: high non-alnum ratio often signals bad extraction.
    Lower is better.
    """
    if not text:
        return 1.0
    allowed = set(".,;:'\"()[]-")
    non = 0
    for c in text:
        if c.isalnum() or c.isspace() or c in allowed:
            continue
        non += 1
    return non / max(1, len(text))
