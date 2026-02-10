from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AtlasConfig:
    # Paths
    project_root: Path = Path(".")
    raw_dir: Path = Path("data/raw")
    out_dir: Path = Path("out")

    # Chunking
    chunk_words: int = 350
    chunk_overlap: int = 50

    # Web crawling
    web_concurrency: int = 40
    web_timeout_s: int = 25
    web_max_retries: int = 2
    web_delay_s: float = 0.0  # add 0.05–0.2 if you want politeness

    # OpenSearch
    opensearch_url: str = "http://localhost:9200"
    opensearch_index: str = "atlas_chunks"
