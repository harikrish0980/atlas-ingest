# atlas/eval/retrieval_eval.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from opensearchpy import OpenSearch


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _search(client: OpenSearch, index_name: str, query: str, k: int) -> List[Dict[str, Any]]:
    body = {
        "size": k,
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["text^2", "source_uri"],
            }
        }
    }
    resp = client.search(index=index_name, body=body)
    hits = resp.get("hits", {}).get("hits", [])
    return hits


def run_retrieval_eval(
    gold_queries_jsonl: Path,
    out_md: Path,
    opensearch_url: str,
    index_name: str,
    k: int = 5,
) -> Dict[str, Any]:
    client = OpenSearch(opensearch_url, verify_certs=False)
    gold = _read_jsonl(gold_queries_jsonl)

    total = 0
    hit = 0
    details: List[Dict[str, Any]] = []

    for g in gold:
        total += 1
        q = g["query"]
        expected = (g.get("expected_source_contains") or "").strip()
        expected_lower = expected.lower()

        hits = _search(client, index_name, q, k=k)
        joined = " ".join((h.get("_source", {}).get("text") or "") for h in hits).lower()
        ok = True if not expected_lower else (expected_lower in joined)

        if ok:
            hit += 1

        details.append({
            "query": q,
            "expected_source_contains": expected,
            "ok": ok,
            "top_hits": [
                {
                    "chunk_id": h.get("_source", {}).get("chunk_id"),
                    "source_uri": h.get("_source", {}).get("source_uri"),
                }
                for h in hits[: min(3, len(hits))]
            ]
        })

    recall_at_k = (hit / total) if total else 0.0
    report = {"k": k, "total": total, "hit": hit, "recall_at_k": recall_at_k, "details": details}

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(_render_md(report), encoding="utf-8")
    return report


def _render_md(report: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Retrieval Evaluation Report\n")
    lines.append(f"- Index: **atlas_chunks**\n")
    lines.append(f"- k: **{report['k']}**\n")
    lines.append(f"- Queries: **{report['total']}**\n")
    lines.append(f"- Hits: **{report['hit']}**\n")
    lines.append(f"- Recall@{report['k']}: **{report['recall_at_k']:.3f}**\n")

    lines.append("\n## Per-query detail (top 3 hits)\n")
    for d in report["details"]:
        lines.append(f"\n### Query: {d['query']}\n")
        if d["expected_source_contains"]:
            lines.append(f"- Expected contains: `{d['expected_source_contains']}`\n")
        lines.append(f"- OK: **{d['ok']}**\n")
        for h in d["top_hits"]:
            lines.append(f"  - {h.get('chunk_id')} — {h.get('source_uri')}\n")
    return "".join(lines)
