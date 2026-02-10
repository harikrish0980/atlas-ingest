# atlas/eval/web_eval.py
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, List
import math

from atlas.store.jsonl_writer import read_jsonl


def _percentile(xs: List[float], p: float) -> float:
    if not xs:
        return float("nan")
    xs = sorted(xs)
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    if f == c:
        return xs[f]
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def run_web_eval(chunks_jsonl: Path, out_md: Path) -> Dict[str, Any]:
    rows = read_jsonl(chunks_jsonl)
    web = [r for r in rows if r.get("source_type") == "web"]

    docs = set()
    langs = Counter()
    gib_scores: List[float] = []
    char_lens: List[int] = []
    empty = 0

    for r in web:
        docs.add(r.get("doc_id"))
        text = (r.get("text") or "").strip()
        if not text:
            empty += 1

        q = r.get("quality") or {}
        langs[q.get("lang", "unknown")] += 1
        gs = q.get("gibberish_score")
        if gs is not None:
            gib_scores.append(float(gs))
        cl = q.get("char_len")
        if cl is not None:
            char_lens.append(int(cl))

    stats = {
        "web_docs": len(docs),
        "web_chunks": len(web),
        "empty_web_chunks": empty,
        "top_langs": dict(langs.most_common(10)),
        "gibberish_score": {
            "mean": (sum(gib_scores) / len(gib_scores)) if gib_scores else float("nan"),
            "p50": _percentile(gib_scores, 0.50),
            "p90": _percentile(gib_scores, 0.90),
        },
        "char_len": {
            "mean": (sum(char_lens) / len(char_lens)) if char_lens else float("nan"),
            "p50": _percentile([float(x) for x in char_lens], 0.50),
            "p90": _percentile([float(x) for x in char_lens], 0.90),
        },
    }

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(_render_md(stats), encoding="utf-8")
    return stats


def _render_md(stats: Dict[str, Any]) -> str:
    def f(x: float) -> str:
        if x != x:
            return "n/a"
        return f"{x:.4f}"

    lines = []
    lines.append("# Web Extraction Evaluation Report\n")
    lines.append(f"- Web documents: **{stats['web_docs']}**\n")
    lines.append(f"- Web chunks: **{stats['web_chunks']}**\n")
    lines.append(f"- Empty web chunks: **{stats['empty_web_chunks']}**\n")

    lines.append("\n## Top Languages\n")
    for k, v in stats["top_langs"].items():
        lines.append(f"- {k}: {v}\n")

    lines.append("\n## Gibberish Score\n")
    gs = stats["gibberish_score"]
    lines.append(f"- mean: {f(gs['mean'])}\n")
    lines.append(f"- p50:  {f(gs['p50'])}\n")
    lines.append(f"- p90:  {f(gs['p90'])}\n")

    lines.append("\n## Chunk Length (chars)\n")
    cl = stats["char_len"]
    lines.append(f"- mean: {f(cl['mean'])}\n")
    lines.append(f"- p50:  {f(cl['p50'])}\n")
    lines.append(f"- p90:  {f(cl['p90'])}\n")
    return "".join(lines)
