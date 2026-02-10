# atlas/cli.py
import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from langdetect import LangDetectException, detect
from rich import print
from rich.progress import track

from atlas.acquire.pdf_downloader import download_pdf
from atlas.acquire.web_crawler import crawl_urls
from atlas.chunk.chunker import chunk_words
from atlas.clean.normalize import gibberish_score, normalize_text
from atlas.clean.pdf_header_footer import PageText, remove_repeated_headers_footers
from atlas.config import AtlasConfig
from atlas.dedupe.exact import dedupe_exact, sha256_text
from atlas.dedupe.simhash import dedupe_near_simhash, simhash64
from atlas.extract.pdf_extract import PDFExtractResult, extract_pdf
from atlas.extract.web_extract import extract_main_text
from atlas.store.jsonl_writer import read_jsonl, write_jsonl
from atlas.store.metadata_sqlite import init_db, insert_chunks, upsert_doc
from atlas.store.opensearch_index import index_chunks

from atlas.eval.extraction_eval import run_extraction_eval
from atlas.eval.web_eval import run_web_eval
from atlas.eval.retrieval_eval import run_retrieval_eval
from atlas.dataset.build_citation_qa import build_citation_qa_dataset

app = typer.Typer(add_completion=False)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_lang(text: str) -> str:
    try:
        return detect(text[:2000])
    except LangDetectException:
        return "unknown"


def make_doc_id(source_uri: str, text_sample: str) -> str:
    h = hashlib.sha256((source_uri + "|" + text_sample).encode("utf-8", errors="ignore")).hexdigest()
    return "sha256:" + h


def make_chunk_id(doc_id: str, chunk_text: str, chunk_index: int) -> str:
    h = hashlib.sha256(
        (doc_id + "|" + str(chunk_index) + "|" + chunk_text).encode("utf-8", errors="ignore")
    ).hexdigest()
    return "sha256:" + h


def load_lines(p: Path) -> List[str]:
    if not p:
        return []
    return [
        ln.strip()
        for ln in p.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def build_pdf_chunks(
    pdf_path: Path,
    cfg: AtlasConfig,
    ingested_at: str,
) -> tuple[str, Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    result: PDFExtractResult = extract_pdf(pdf_path)

    pages = [PageText(page=p.page, text=p.text) for p in result.pages]
    pages_clean = remove_repeated_headers_footers(pages, min_repeat_ratio=0.6, lines_to_check=2)

    combined = "\n\n".join(p.text for p in pages_clean)
    combined = normalize_text(combined)

    doc_id = make_doc_id(str(pdf_path), combined[:5000])

    doc_meta = {
        "doc_id": doc_id,
        "source_type": "pdf",
        "source_uri": str(pdf_path),
        "page_count": result.page_count,
        "engine": result.engine,
        "ingested_at": ingested_at,
    }

    chunks = chunk_words(combined, chunk_size=cfg.chunk_words, overlap=cfg.chunk_overlap)

    jsonl_rows: List[Dict[str, Any]] = []
    sqlite_rows: List[Dict[str, Any]] = []

    for idx, ch in enumerate(chunks):
        ch = normalize_text(ch)
        if not ch:
            continue

        exact = sha256_text(ch)
        simh = simhash64(ch)

        row = {
            "chunk_id": make_chunk_id(doc_id, ch[:4000], idx),
            "doc_id": doc_id,
            "chunk_index": idx,
            "source_type": "pdf",
            "source_uri": str(pdf_path),
            "page_start": None,
            "page_end": None,
            "text": ch,
            "quality": {
                "lang": safe_lang(ch),
                "gibberish_score": round(gibberish_score(ch), 4),
                "char_len": len(ch),
                "word_len": len(ch.split()),
            },
            "dedupe": {"exact_hash": exact, "simhash64": simh},
            "timestamps": {"ingested_at": ingested_at},
        }
        jsonl_rows.append(row)

        sqlite_rows.append(
            {
                "chunk_id": row["chunk_id"],
                "doc_id": doc_id,
                "chunk_index": idx,
                "source_uri": str(pdf_path),
                "page_start": None,
                "page_end": None,
                "exact_hash": exact,
                "simhash64": str(simh) if simh is not None else None,
                "char_len": row["quality"]["char_len"],
                "word_len": row["quality"]["word_len"],
                "lang": row["quality"]["lang"],
                "gibberish_score": row["quality"]["gibberish_score"],
                "ingested_at": ingested_at,
            }
        )

    return doc_id, doc_meta, jsonl_rows, sqlite_rows


async def build_web_chunks_async(
    urls: List[str],
    cfg: AtlasConfig,
    ingested_at: str,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    results = await crawl_urls(
        urls,
        concurrency=cfg.web_concurrency,
        timeout_s=cfg.web_timeout_s,
        retries=cfg.web_max_retries,
        delay_s=cfg.web_delay_s,
    )

    docs_meta: List[Dict[str, Any]] = []
    jsonl_rows: List[Dict[str, Any]] = []
    sqlite_rows: List[Dict[str, Any]] = []

    for r in results:
        if not r.ok:
            continue

        ex = extract_main_text(r.url, r.html)
        cleaned = normalize_text(ex.raw_text)
        if not cleaned:
            continue

        doc_id = make_doc_id(ex.source_uri, cleaned[:5000])

        docs_meta.append(
            {
                "doc_id": doc_id,
                "source_type": "web",
                "source_uri": ex.source_uri,
                "page_count": None,
                "engine": "trafilatura",
                "ingested_at": ingested_at,
            }
        )

        chunks = chunk_words(cleaned, chunk_size=cfg.chunk_words, overlap=cfg.chunk_overlap)

        for idx, ch in enumerate(chunks):
            ch = normalize_text(ch)
            if not ch:
                continue

            exact = sha256_text(ch)
            simh = simhash64(ch)

            row = {
                "chunk_id": make_chunk_id(doc_id, ch[:4000], idx),
                "doc_id": doc_id,
                "chunk_index": idx,
                "source_type": "web",
                "source_uri": ex.source_uri,
                "page_start": None,
                "page_end": None,
                "text": ch,
                "quality": {
                    "lang": safe_lang(ch),
                    "gibberish_score": round(gibberish_score(ch), 4),
                    "char_len": len(ch),
                    "word_len": len(ch.split()),
                },
                "dedupe": {"exact_hash": exact, "simhash64": simh},
                "timestamps": {"ingested_at": ingested_at},
            }
            jsonl_rows.append(row)

            sqlite_rows.append(
                {
                    "chunk_id": row["chunk_id"],
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "source_uri": ex.source_uri,
                    "page_start": None,
                    "page_end": None,
                    "exact_hash": exact,
                    "simhash64": str(simh) if simh is not None else None,
                    "char_len": row["quality"]["char_len"],
                    "word_len": row["quality"]["word_len"],
                    "lang": row["quality"]["lang"],
                    "gibberish_score": row["quality"]["gibberish_score"],
                    "ingested_at": ingested_at,
                }
            )

    return docs_meta, jsonl_rows, sqlite_rows


@app.command()
def ingest(
    pdf_dir: Optional[Path] = typer.Option(None, "--pdf-dir", help="Folder containing PDFs (e.g., data/raw/pdfs)"),
    pdf_urls: Optional[Path] = typer.Option(None, "--pdf-urls", help="Text file with PDF URLs (one per line)"),
    urls: Optional[Path] = typer.Option(None, "--urls", help="Text file with web URLs (one per line)"),
    out: Path = typer.Option(Path("out"), "--out", help="Output directory"),
    near_dup_threshold: int = typer.Option(3, "--near-dup-threshold", help="SimHash hamming threshold for near-duplicate removal"),
):
    cfg = AtlasConfig(out_dir=out)
    out.mkdir(parents=True, exist_ok=True)

    chunks_jsonl: List[Dict[str, Any]] = []
    chunks_sqlite: List[Dict[str, Any]] = []
    docs_meta: List[Dict[str, Any]] = []

    ingested_at = now_iso()

    if pdf_urls:
        pdf_url_list = load_lines(pdf_urls)
        dl_dir = Path("data/raw/pdfs")
        print(f"[bold]Downloading PDFs:[/bold] {len(pdf_url_list)} -> {dl_dir}")
        for u in track(pdf_url_list, description="Downloading PDFs"):
            try:
                download_pdf(u, dl_dir)
            except Exception as e:
                print(f"[yellow]PDF download failed[/yellow] {u}: {e}")

    if pdf_dir and pdf_dir.exists():
        pdf_files = sorted(pdf_dir.glob("*.pdf"))
        print(f"[bold]PDFs found:[/bold] {len(pdf_files)}")
        for p in track(pdf_files, description="Processing PDFs"):
            try:
                _, doc_meta, jsonl_rows, sqlite_rows = build_pdf_chunks(p, cfg, ingested_at)
                docs_meta.append(doc_meta)
                chunks_jsonl.extend(jsonl_rows)
                chunks_sqlite.extend(sqlite_rows)
            except Exception as e:
                print(f"[yellow]PDF ingest failed[/yellow] {p}: {e}")

    if urls:
        web_urls = load_lines(urls)
        print(f"[bold]Web URLs found:[/bold] {len(web_urls)}")
        try:
            dm, jr, sr = asyncio.run(build_web_chunks_async(web_urls, cfg, ingested_at))
            docs_meta.extend(dm)
            chunks_jsonl.extend(jr)
            chunks_sqlite.extend(sr)
        except Exception as e:
            print(f"[yellow]Web ingest failed[/yellow]: {e}")

    if not chunks_jsonl:
        print("[red]No chunks produced.[/red] Check your inputs.")
        raise typer.Exit(code=1)

    before = len(chunks_jsonl)
    kept_jsonl, removed_exact = dedupe_exact(
        [{**r, "exact_hash": r["dedupe"]["exact_hash"]} for r in chunks_jsonl],
        hash_field="exact_hash",
    )

    kept_chunk_ids = set(r["chunk_id"] for r in kept_jsonl)
    chunks_jsonl = [r for r in chunks_jsonl if r["chunk_id"] in kept_chunk_ids]
    chunks_sqlite = [r for r in chunks_sqlite if r["chunk_id"] in kept_chunk_ids]

    simhashes = [r["dedupe"]["simhash64"] for r in chunks_jsonl]
    keep_mask = dedupe_near_simhash(simhashes, threshold=near_dup_threshold)
    chunks_jsonl = [r for r, k in zip(chunks_jsonl, keep_mask) if k]
    kept_ids_after_near = {r["chunk_id"] for r in chunks_jsonl}
    chunks_sqlite = [r for r in chunks_sqlite if r["chunk_id"] in kept_ids_after_near]

    after = len(chunks_jsonl)
    removed_near = before - removed_exact - after

    chunks_path = out / "chunks.jsonl"
    write_jsonl(chunks_path, chunks_jsonl)

    db_path = out / "atlas.db"
    init_db(db_path)

    for d in docs_meta:
        upsert_doc(
            db_path=db_path,
            doc_id=d["doc_id"],
            source_type=d["source_type"],
            source_uri=d["source_uri"],
            ingested_at=d["ingested_at"],
            page_count=d.get("page_count"),
            engine=d.get("engine"),
        )

    insert_chunks(db_path, chunks_sqlite)

    print("\n[bold green]Ingest complete[/bold green]")
    print(f"- Chunks before dedupe: {before}")
    print(f"- Removed exact dupes:  {removed_exact}")
    print(f"- Removed near dupes:   {max(0, removed_near)}")
    print(f"- Chunks kept:          {after}")
    print(f"- Wrote: {chunks_path}")
    print(f"- Wrote: {db_path}")


@app.command()
def index(
    infile: Path = typer.Option(..., "--in", help="Input chunks.jsonl"),
    opensearch_url: str = typer.Option(AtlasConfig().opensearch_url, "--opensearch-url", help="OpenSearch URL"),
    index_name: str = typer.Option(AtlasConfig().opensearch_index, "--index-name", help="OpenSearch index name"),
):
    rows = read_jsonl(infile)
    flat = []
    for r in rows:
        flat.append(
            {
                "chunk_id": r["chunk_id"],
                "doc_id": r["doc_id"],
                "source_type": r["source_type"],
                "source_uri": r["source_uri"],
                "page_start": r.get("page_start"),
                "page_end": r.get("page_end"),
                "lang": r["quality"]["lang"],
                "text": r["text"],
                "ingested_at": r["timestamps"]["ingested_at"],
            }
        )

    n = index_chunks(opensearch_url=opensearch_url, index_name=index_name, chunks=flat)
    print(f"[bold green]Indexed[/bold green] {n} chunks into {index_name} at {opensearch_url}")


@app.command()
def eval(
    out: Path = typer.Option(Path("out"), "--out", help="Output directory (where chunks.jsonl lives)"),
    opensearch_url: str = typer.Option(AtlasConfig().opensearch_url, "--opensearch-url", help="OpenSearch URL"),
    index_name: str = typer.Option(AtlasConfig().opensearch_index, "--index-name", help="OpenSearch index name"),
    gold: Path = typer.Option(Path("atlas/eval/gold_queries.jsonl"), "--gold", help="Gold queries JSONL for retrieval eval"),
    k: int = typer.Option(5, "--k", help="Top-K for Recall@K"),
):
    chunks_jsonl = out / "chunks.jsonl"
    if not chunks_jsonl.exists():
        raise typer.Exit(code=1)

    r1 = run_extraction_eval(chunks_jsonl, out / "report_extraction.md")
    r2 = run_web_eval(chunks_jsonl, out / "report_web.md")

    if gold.exists():
        r3 = run_retrieval_eval(
            gold_queries_jsonl=gold,
            out_md=out / "report_retrieval.md",
            opensearch_url=opensearch_url,
            index_name=index_name,
            k=k,
        )
        print("[bold green]Eval complete[/bold green]")
        print(f"- Wrote: {out / 'report_extraction.md'}")
        print(f"- Wrote: {out / 'report_web.md'}")
        print(f"- Wrote: {out / 'report_retrieval.md'}")
    else:
        print("[yellow]Gold queries file not found; skipping retrieval eval.[/yellow]")
        print("[bold green]Eval complete[/bold green]")
        print(f"- Wrote: {out / 'report_extraction.md'}")
        print(f"- Wrote: {out / 'report_web.md'}")


@app.command()
def dataset(
    infile: Path = typer.Option(..., "--in", help="Input chunks.jsonl"),
    outfile: Path = typer.Option(Path("out/sft_citation_qa.jsonl"), "--out", help="Output dataset JSONL"),
    max_rows: int = typer.Option(300, "--max-rows", help="Max dataset rows"),
    min_chars: int = typer.Option(200, "--min-chars", help="Min chars required per chunk"),
):
    stats = build_citation_qa_dataset(
        chunks_jsonl=infile,
        out_jsonl=outfile,
        max_rows=max_rows,
        min_chars=min_chars,
    )
    print("[bold green]Dataset build complete[/bold green]")
    print(f"- Wrote: {outfile}")
    print(f"- Rows: {stats['written']} (skipped_short={stats['skipped_short']})")


if __name__ == "__main__":
    app()
