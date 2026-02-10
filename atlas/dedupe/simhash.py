from __future__ import annotations
from typing import Iterable, List
import re


_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def _hash64(s: str) -> int:
    # Simple stable 64-bit hash (FNV-1a)
    h = 1469598103934665603
    fnv_prime = 1099511628211
    for b in s.encode("utf-8", errors="ignore"):
        h ^= b
        h = (h * fnv_prime) & 0xFFFFFFFFFFFFFFFF
    return h


def simhash64(text: str) -> int:
    """
    Compute 64-bit SimHash for text.
    """
    tokens = _tokenize(text)
    if not tokens:
        return 0

    v = [0] * 64
    for tok in tokens:
        h = _hash64(tok)
        for i in range(64):
            bit = (h >> i) & 1
            v[i] += 1 if bit else -1

    out = 0
    for i in range(64):
        if v[i] > 0:
            out |= (1 << i)
    return out


def hamming_distance64(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def dedupe_near_simhash(
    simhashes: List[int],
    threshold: int = 3,
) -> List[bool]:
    """
    Given simhash list, return keep_mask (True=keep, False=drop).
    O(n^2) – fine for demo sizes. For huge scale you’d do bucketing/LSH.
    """
    keep = [True] * len(simhashes)
    for i in range(len(simhashes)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(simhashes)):
            if not keep[j]:
                continue
            if hamming_distance64(simhashes[i], simhashes[j]) <= threshold:
                keep[j] = False
    return keep
