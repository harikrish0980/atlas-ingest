from __future__ import annotations
from pathlib import Path
import re
import httpx


def _safe_filename_from_url(url: str) -> str:
    # Keep it simple and safe
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.strip())
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    # Limit length
    return name[:180]


def download_pdf(url: str, out_dir: Path, timeout_s: int = 30) -> Path:
    """
    Download a PDF from URL into out_dir. Returns local file path.
    Skips download if file already exists.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / _safe_filename_from_url(url)

    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path

    with httpx.Client(follow_redirects=True, timeout=timeout_s) as client:
        r = client.get(url)
        r.raise_for_status()

        # Basic content-type check (not strict)
        if "pdf" not in (r.headers.get("content-type") or "").lower():
            # Still write — many servers mislabel
            pass

        out_path.write_bytes(r.content)

    return out_path
