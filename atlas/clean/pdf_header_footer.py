from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Dict
from collections import Counter


@dataclass
class PageText:
    page: int
    text: str


def _first_lines(text: str, n: int = 2) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[:n]


def _last_lines(text: str, n: int = 2) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-n:] if len(lines) >= n else lines


def remove_repeated_headers_footers(
    pages: List[PageText],
    min_repeat_ratio: float = 0.6,
    lines_to_check: int = 2,
) -> List[PageText]:
    """
    Heuristic header/footer removal:
    - Detect lines that repeat across many pages in the first/last N lines.
    - Remove those lines from each page.
    """
    if not pages:
        return pages

    first_counter = Counter()
    last_counter = Counter()

    for p in pages:
        for ln in _first_lines(p.text, lines_to_check):
            first_counter[ln] += 1
        for ln in _last_lines(p.text, lines_to_check):
            last_counter[ln] += 1

    page_count = len(pages)
    min_count = max(2, int(page_count * min_repeat_ratio))

    repeated_first = {ln for ln, c in first_counter.items() if c >= min_count and len(ln) >= 6}
    repeated_last = {ln for ln, c in last_counter.items() if c >= min_count and len(ln) >= 6}

    cleaned: List[PageText] = []
    for p in pages:
        lines = p.text.splitlines()
        new_lines = []
        for ln in lines:
            s = ln.strip()
            if s in repeated_first or s in repeated_last:
                continue
            new_lines.append(ln)
        cleaned.append(PageText(page=p.page, text="\n".join(new_lines).strip()))

    return cleaned
