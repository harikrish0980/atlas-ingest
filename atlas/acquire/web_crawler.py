from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple
import httpx


@dataclass
class CrawlResult:
    url: str
    ok: bool
    status_code: Optional[int]
    html: str
    error: Optional[str] = None


async def _fetch_one(
    client: httpx.AsyncClient,
    url: str,
    retries: int,
    delay_s: float,
) -> CrawlResult:
    last_err = None
    for attempt in range(retries + 1):
        try:
            if delay_s > 0:
                await asyncio.sleep(delay_s)

            r = await client.get(url)
            status = r.status_code
            if status >= 400:
                return CrawlResult(url=url, ok=False, status_code=status, html="", error=f"HTTP {status}")
            html = r.text
            return CrawlResult(url=url, ok=True, status_code=status, html=html)
        except Exception as e:
            last_err = str(e)
            # small backoff
            await asyncio.sleep(min(1.5 * (attempt + 1), 5.0))
    return CrawlResult(url=url, ok=False, status_code=None, html="", error=last_err)


async def crawl_urls(
    urls: Iterable[str],
    concurrency: int = 40,
    timeout_s: int = 25,
    retries: int = 2,
    delay_s: float = 0.0,
    user_agent: str = "AtlasIngest/1.0",
) -> List[CrawlResult]:
    """
    Fetch many URLs concurrently. Returns list of CrawlResult.
    """
    url_list = [u.strip() for u in urls if u and u.strip() and not u.strip().startswith("#")]
    limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)

    async with httpx.AsyncClient(
        timeout=timeout_s,
        follow_redirects=True,
        limits=limits,
        headers={"User-Agent": user_agent},
    ) as client:
        sem = asyncio.Semaphore(concurrency)

        async def bound_fetch(u: str) -> CrawlResult:
            async with sem:
                return await _fetch_one(client, u, retries=retries, delay_s=delay_s)

        tasks = [asyncio.create_task(bound_fetch(u)) for u in url_list]
        results = await asyncio.gather(*tasks)

    return results
