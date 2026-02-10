from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

import fitz  # PyMuPDF
import pdfplumber


@dataclass
class PDFPageText:
    page: int
    text: str


@dataclass
class PDFExtractResult:
    source_uri: str
    page_count: int
    pages: List[PDFPageText]
    raw_text: str
    engine: str  # "pymupdf" or "pdfplumber"


def _extract_with_pymupdf(pdf_bytes: bytes, source_uri: str) -> PDFExtractResult:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: List[PDFPageText] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        t = page.get_text("text") or ""
        pages.append(PDFPageText(page=i + 1, text=t))
    raw = "\n\n".join(p.text for p in pages).strip()
    return PDFExtractResult(
        source_uri=source_uri,
        page_count=doc.page_count,
        pages=pages,
        raw_text=raw,
        engine="pymupdf",
    )


def _extract_with_pdfplumber(pdf_path: Path, source_uri: str) -> PDFExtractResult:
    pages: List[PDFPageText] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, p in enumerate(pdf.pages, start=1):
            t = p.extract_text() or ""
            pages.append(PDFPageText(page=i, text=t))
        raw = "\n\n".join(pp.text for pp in pages).strip()
        return PDFExtractResult(
            source_uri=source_uri,
            page_count=len(pdf.pages),
            pages=pages,
            raw_text=raw,
            engine="pdfplumber",
        )


def extract_pdf(
    pdf_path: Path,
    fallback_if_short_chars: int = 800,
) -> PDFExtractResult:
    """
    Extract text from PDF. Uses PyMuPDF first; falls back to pdfplumber if extraction is too short.
    """
    pdf_bytes = pdf_path.read_bytes()
    first = _extract_with_pymupdf(pdf_bytes, source_uri=str(pdf_path))

    # Fallback heuristic: if almost empty, try pdfplumber
    if len(first.raw_text) < fallback_if_short_chars:
        try:
            second = _extract_with_pdfplumber(pdf_path, source_uri=str(pdf_path))
            # Use whichever is better
            if len(second.raw_text) > len(first.raw_text):
                return second
        except Exception:
            pass

    return first
