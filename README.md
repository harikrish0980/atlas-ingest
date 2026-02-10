# AtlasIngest

AtlasIngest is a production-style PDF + Web document ingestion pipeline that demonstrates how to build high-quality text corpora for retrieval, evaluation, and post-training (SFT) workflows.

## Overview
This project shows how to ingest heterogeneous document sources, clean and normalize text, chunk and deduplicate content, evaluate extraction and retrieval quality, and generate citation-style datasets suitable for post-training large language models.

## Architecture
PDFs and Web URLs are acquired, extracted, cleaned, chunked, deduplicated, stored as JSONL and SQLite metadata, indexed into OpenSearch, evaluated, and finally converted into post-training datasets.

## Features
- PDF and web ingestion
- Async web crawling with retries
- Robust text extraction with fallbacks
- Header and footer removal for PDFs
- Overlapping chunking
- Exact and near-duplicate removal using SimHash
- JSONL corpus + SQLite metadata store
- OpenSearch indexing
- Extraction and retrieval evaluation
- Citation-style QA dataset generation

## Quickstart
1. Ingest documents
2. Index into OpenSearch
3. Run evaluation
4. Build post-training dataset

## Results
- PDFs ingested: 8
- Web pages ingested: 7
- Chunks before dedupe: 325
- Chunks kept: 305
- Retrieval Recall@5: 0.60
- Dataset rows generated: 300

## Evaluation
Includes extraction quality metrics, web extraction analysis, and retrieval Recall@K using gold queries.

## Post-training Dataset
Generates citation-style QA examples with prompt, context, answer, and source citation.

## Scaling Notes
Designed to mirror large-scale ingestion systems and can be extended to distributed crawlers, object storage, and large-scale indexing.

## Roadmap
- OCR for scanned PDFs
- Distributed processing
- Embedding-based retrieval

