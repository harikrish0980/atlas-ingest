from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Dict, Any, Iterable, Optional


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS docs (
        doc_id TEXT PRIMARY KEY,
        source_type TEXT NOT NULL,
        source_uri TEXT NOT NULL,
        page_count INTEGER,
        engine TEXT,
        ingested_at TEXT NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        doc_id TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        source_uri TEXT NOT NULL,
        page_start INTEGER,
        page_end INTEGER,
        exact_hash TEXT,
        simhash64 TEXT,
        char_len INTEGER,
        word_len INTEGER,
        lang TEXT,
        gibberish_score REAL,
        ingested_at TEXT NOT NULL,
        FOREIGN KEY(doc_id) REFERENCES docs(doc_id)
    )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_exact_hash ON chunks(exact_hash)")
    con.commit()
    con.close()


def upsert_doc(
    db_path: Path,
    doc_id: str,
    source_type: str,
    source_uri: str,
    ingested_at: str,
    page_count: Optional[int] = None,
    engine: Optional[str] = None,
) -> None:
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.execute("""
    INSERT INTO docs(doc_id, source_type, source_uri, page_count, engine, ingested_at)
    VALUES(?,?,?,?,?,?)
    ON CONFLICT(doc_id) DO UPDATE SET
        source_type=excluded.source_type,
        source_uri=excluded.source_uri,
        page_count=excluded.page_count,
        engine=excluded.engine,
        ingested_at=excluded.ingested_at
    """, (doc_id, source_type, source_uri, page_count, engine, ingested_at))
    con.commit()
    con.close()


def insert_chunks(db_path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    con = sqlite3.connect(str(db_path))
    cur = con.cursor()
    cur.executemany("""
    INSERT OR REPLACE INTO chunks(
        chunk_id, doc_id, chunk_index, source_uri, page_start, page_end,
        exact_hash, simhash64, char_len, word_len, lang, gibberish_score, ingested_at
    )
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [
        (
            r["chunk_id"], r["doc_id"], r["chunk_index"], r["source_uri"],
            r.get("page_start"), r.get("page_end"),
            r.get("exact_hash"), str(r.get("simhash64")) if r.get("simhash64") is not None else None,
            r.get("char_len"), r.get("word_len"),
            r.get("lang"), r.get("gibberish_score"),
            r["ingested_at"]
        )
        for r in rows
    ])
    con.commit()
    con.close()
