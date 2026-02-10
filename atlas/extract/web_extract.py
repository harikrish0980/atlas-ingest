from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import trafilatura


@dataclass
class WebExtractResult:
    source_uri: str
    title: Optional[str]
    raw_text: str


def extract_main_text(url: str, html: str) -> WebExtractResult:
    """
    Extract main content text from HTML using trafilatura.
    """
    downloaded = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        favor_recall=True,
    )
    text = downloaded or ""
    # trafilatura has metadata extraction but keep simple
    return WebExtractResult(source_uri=url, title=None, raw_text=text.strip())
