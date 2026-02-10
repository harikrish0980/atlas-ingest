# AtlasIngest

AtlasIngest is a production-style "PDF + Web document ingestion pipeline" that demonstrates how to build high-quality text corpora for "retrieval, evaluation, and post-training  workflows".

The project is intentionally small enough to run on a laptop, while mirroring the architecture and design patterns used in "large-scale document processing systems".

---

## Why this project exists

Modern AI systems depend on large, clean, deduplicated document corpora.  
This project demonstrates how to:

- ingest heterogeneous sources (PDFs + web)
- clean and normalize raw text
- chunk documents for retrieval and training
- remove exact and near-duplicate content
- evaluate extraction and retrieval quality
- generate citation-style post-training datasets

AtlasIngest is designed as a ""data-engineering-first pipeline", not a demo script.

---

## High-level architecture

```
flowchart TD
  A[PDFs / Web URLs] --> B[Acquire]
  B --> C[Extract]
  C --> D[Clean & Normalize]
  D --> E[Chunk]
  E --> F[Deduplicate]
  F --> G[JSONL Corpus]
  F --> H[SQLite Metadata Store]
  G --> I[OpenSearch Index]
  I --> J[Retrieval Evaluation]
  G --> K[Post-training Dataset]
```

---

## Key features

- Multi-source ingestion (PDFs + Web)
- Async web crawling with retries and rate limits
- Robust PDF extraction with engine fallback
- Repeated header/footer removal for PDFs
- Overlapping chunking for retrieval-friendly text blocks
- Exact deduplication via SHA-256
- Near-duplicate removal via 64-bit SimHash
- Portable JSONL corpus format
- SQLite metadata store for audit and debugging
- OpenSearch indexing for retrieval
- Extraction, web, and retrieval evaluation
- Citation-style post-training dataset generation

---

## Repository structure

```
atlas-ingest/
  atlas/
    acquire/        # PDF download + async web crawl
    extract/        # PDF + HTML text extraction
    clean/          # Normalization + header/footer removal
    chunk/          # Text chunking
    dedupe/         # Exact + near-duplicate detection
    store/          # JSONL, SQLite, OpenSearch
    eval/           # Extraction, web, retrieval evaluation
    dataset/        # Post-training dataset builder
  data/raw/pdfs/    # Input PDFs
  examples/urls.txt # Web URLs
  out/              # Generated artifacts
```

---

## Requirements

- Python 3.10+
- Docker (optional, for OpenSearch)

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Quickstart

### Ingest documents
```bash
python -m atlas.cli ingest   --pdf-dir data/raw/pdfs   --urls examples/urls.txt   --out out
```

### Index chunks into OpenSearch
```bash
python -m atlas.cli index   --in out/chunks.jsonl   --opensearch-url http://localhost:9200   --index-name atlas_chunks
```

### Run evaluation
```bash
python -m atlas.cli eval   --out out   --gold atlas/eval/gold_queries.jsonl
```

### Build post-training dataset
```bash
python -m atlas.cli dataset   --in out/chunks.jsonl   --out out/sft_citation_qa.jsonl
```

---

## Results (local run)

- PDFs ingested: 8
- Web pages ingested: 7
- Chunks before dedupe: 325
- Chunks kept: 305
- Near-duplicates removed: 20
- Retrieval Recall@5: 0.60 (10 gold queries)
- Post-training dataset rows: 300

Generated artifacts:
- out/chunks.jsonl
- out/atlas.db
- out/report_extraction.md
- out/report_web.md
- out/report_retrieval.md
- out/sft_citation_qa.jsonl

---

## Evaluation methodology

### Extraction evaluation
- Chunk length distribution (characters and words)
- Language distribution
- Gibberish score percentiles
- Empty chunk rate

### Web evaluation
- Web-only extraction quality
- Language and text quality metrics

### Retrieval evaluation
- OpenSearch BM25 retrieval
- Recall@K using curated gold queries
- Per-query hit inspection

All evaluation outputs are written as Markdown reports under the out/ directory.

---

## Post-training dataset generation

The dataset builder creates citation-style QA examples directly from the ingested corpus.

Each record includes:
- prompt
- context
- question
- answer
- citation (source URI + chunk ID)

This mirrors the structure commonly used in supervised fine-tuning and post-training pipelines.

---

## Design choices

- Idempotent document and chunk IDs using SHA-256
- SimHash for efficient near-duplicate detection
- JSONL as a portable corpus exchange format
- SQLite as a lightweight metadata and audit store
- Evaluation treated as a first-class pipeline stage

---

## Scaling notes

At large scale, this pipeline maps directly to:
- distributed crawlers and extractors
- object storage for raw and derived artifacts
- sharded metadata stores
- incremental indexing pipelines
- continuous evaluation and dataset refresh

The local implementation is intentionally simple, but the architecture is production-aligned.

---

## Roadmap

- OCR support for scanned PDFs
- Distributed worker execution
- Embedding-based retrieval
- Active learning for dataset curation

---

