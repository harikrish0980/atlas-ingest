from __future__ import annotations
from typing import Dict, Any, Iterable, Optional
from opensearchpy import OpenSearch, helpers


def create_index_if_missing(client: OpenSearch, index_name: str) -> None:
    if client.indices.exists(index=index_name):
        return

    mapping = {
        "settings": {"index": {"number_of_shards": 1, "number_of_replicas": 0}},
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "doc_id": {"type": "keyword"},
                "source_type": {"type": "keyword"},
                "source_uri": {"type": "keyword"},
                "page_start": {"type": "integer"},
                "page_end": {"type": "integer"},
                "lang": {"type": "keyword"},
                "text": {"type": "text"},
                "ingested_at": {"type": "date"},
            }
        },
    }
    client.indices.create(index=index_name, body=mapping)


def index_chunks(
    opensearch_url: str,
    index_name: str,
    chunks: Iterable[Dict[str, Any]],
    batch_size: int = 500,
) -> int:
    """
    Bulk index chunks into OpenSearch. Returns number indexed.
    """
    client = OpenSearch(opensearch_url, verify_certs=False)
    create_index_if_missing(client, index_name)

    actions = []
    total = 0

    def flush():
        nonlocal actions, total
        if not actions:
            return
        helpers.bulk(client, actions)
        total += len(actions)
        actions = []

    for c in chunks:
        doc = {
            "chunk_id": c.get("chunk_id"),
            "doc_id": c.get("doc_id"),
            "source_type": c.get("source_type"),
            "source_uri": c.get("source_uri"),
            "page_start": c.get("page_start"),
            "page_end": c.get("page_end"),
            "lang": c.get("lang"),
            "text": c.get("text"),
            "ingested_at": c.get("ingested_at"),
        }
        actions.append({
            "_op_type": "index",
            "_index": index_name,
            "_id": doc["chunk_id"],
            "_source": doc,
        })
        if len(actions) >= batch_size:
            flush()

    flush()
    return total
