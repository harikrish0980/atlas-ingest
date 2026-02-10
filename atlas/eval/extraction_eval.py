# atlas/eval/extraction_eval.py
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
import math

from atlas.store.jsonl_writer import read_jsonl


def _percentile(xs: List[float], p: float) -> float:
    if not xs:
        return float("nan")
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs[int(k)]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def run_extraction_eval(chunks_jsonl: Path, out_md: Path) -> Dict[str, Any]:
    rows = read_jsonl(chunks_jsonl)

    docs = set()
    source_types = Counter()
    langs = Counter()
    gib_scores: List[float] = []
    char_lens: List[int] = []
    word_lens: List[int] = []

    empty_text = 0

    for r in rows:
        docs.add(r.get("doc_id"))
        st = r.get("source_type", "unknown")
        source_types[st] += 1

        text = r.get("text") or ""
        if not text.strip():
            empty_text += 1

        q = r.get("quality") or {}
        langs[q.get("lang", "unknown")] += 1

        gs = q.get("gibberish_score")
        if gs is not None:
            gib_scores.append(float(gs))

        cl = q.get("char_len")
        wl = q.get("word_len")
        if cl is not None:
            char_lens.append(int(cl))
        if wl is not None:
            word_lens.append(int(wl))

    stats = {
        "docs_count": len(docs),
        "chunks_count": len(rows),
        "empty_chunks": empty_text,
        "source_types": dict(source_types),
        "top_langs": dict(langs.most_common(10)),
        "gibberish_score": {
            "p50": _percentile(gib_scores, 0.50),
            "p90": _percentile(gib_scores, 0.90),
            "p99": _percentile(gib_scores, 0.99),
            "mean": (sum(gib_scores) / len(gib_scores)) if gib_scores else float("nan"),
        },
        "char_len": {
            "p50": _percentile([float(x) for x in char_lens], 0.50),
            "p90": _percentile([float(x) for x in char_lens], 0.90),
            "p99": _percentile([float(x) for x in char_lens], 0.99),
            "mean": (sum(char_lens) / len(char_lens)) if char_lens else float("nan"),
        },
        "word_len": {
            "p50": _percentile([float(x) for x in word_lens], 0.50),
            "p90": _percentile([float(x) for x in word_lens], 0.90),
            "p99": _percentile([float(x) for x in word_lens], 0.99),
            "mean": (sum(word_lens) / len(word_lens)) if word_lens else float("nan"),
        },
    }

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(_render_md(stats), encoding="utf-8")
    return stats


def _render_md(stats: Dict[str, Any]) -> str:
    def f(x: float) -> str:
        if x != x:  # NaN
            return "n/a"
        return f"{x:.4f}"

    lines = []
    lines.append("# Extraction Evaluation Report\n")
    lines.append("## Counts\n")
    lines.append(f"- Documents: **{stats['docs_count']}**\n")
    lines.append(f"- Chunks: **{stats['chunks_count']}**\n")
    lines.append(f"- Empty chunks: **{stats['empty_chunks']}**\n")

    lines.append("\n## Source Types\n")
    for k, v in stats["source_types"].items():
        lines.append(f"- {k}: {v}\n")

    lines.append("\n## Top Languages (by chunk)\n")
    for k, v in stats["top_langs"].items():
        lines.append(f"- {k}: {v}\n")

    lines.append("\n## Gibberish Score (lower is better)\n")
    gs = stats["gibberish_score"]
    lines.append(f"- mean: {f(gs['mean'])}\n")
    lines.append(f"- p50:  {f(gs['p50'])}\n")
    lines.append(f"- p90:  {f(gs['p90'])}\n")
    lines.append(f"- p99:  {f(gs['p99'])}\n")

    lines.append("\n## Chunk Length (chars)\n")
    cl = stats["char_len"]
    lines.append(f"- mean: {f(cl['mean'])}\n")
    lines.append(f"- p50:  {f(cl['p50'])}\n")
    lines.append(f"- p90:  {f(cl['p90'])}\n")
    lines.append(f"- p99:  {f(cl['p99'])}\n")

    lines.append("\n## Chunk Length (words)\n")
    wl = stats["word_len"]
    lines.append(f"- mean: {f(wl['mean'])}\n")
    lines.append(f"- p50:  {f(wl['p50'])}\n")
    lines.append(f"- p90:  {f(wl['p90'])}\n")
    lines.append(f"- p99:  {f(wl['p99'])}\n")

    return "".join(lines)
