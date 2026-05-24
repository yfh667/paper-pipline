"""IEEE Xplore — pure HTTP via stamp.jsp / stampPDF/getPDF.jsp.

Flow:
  1. DOI -> doi.org -> ieeexplore landing page (extract arnumber from URL)
  2. Visit /document/<arnum>/  (sets Akamai/APM cookies)
  3. Visit /stamp/stamp.jsp?arnumber=<arnum>  (more cookies)
  4. GET /stampPDF/getPDF.jsp?arnumber=<arnum>  -> PDF bytes

On Akamai HTML challenge (APM_DO_NOT_TOUCH), back off + reset session + retry.
"""
from __future__ import annotations

import asyncio
import re
import time
from pathlib import Path

import requests

from .base import Job, PublisherHandler

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class _AkamaiChallenge(Exception):
    """IEEE returned the APM challenge HTML rather than a PDF."""


class IeeeHandler(PublisherHandler):
    tag = "ieee"
    gap_seconds = 60
    HTML_RETRY_SLEEP = 90    # back off this long on APM challenge before retry
    MAX_ATTEMPTS = 2

    def __init__(self, *, out_dir: Path, logger):
        super().__init__(out_dir=out_dir, logger=logger)
        self._session: requests.Session | None = None

    async def setup(self) -> None:
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self.log.info("[ieee] http session ready")

    async def teardown(self) -> None:
        if self._session is not None:
            self._session.close()
            self._session = None

    async def fetch_one(self, job: Job) -> Path:
        return await asyncio.to_thread(self._fetch_sync, job)

    def _fetch_sync(self, job: Job) -> Path:
        assert self._session is not None
        doi = job.doi

        # Resolve DOI -> arnumber once.
        r = self._session.get(f"https://doi.org/{doi}", timeout=60, allow_redirects=True)
        m = re.search(r"/document/(\d+)", r.url)
        if not m:
            raise RuntimeError(f"no arnumber in landing url: {r.url}")
        arnum = m.group(1)

        last_err: str | None = None
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                return self._download_pdf(arnum, job)
            except _AkamaiChallenge as e:
                last_err = str(e)
                if attempt < self.MAX_ATTEMPTS:
                    self.log.warning("[ieee] APM challenge attempt %d for %s — "
                                     "back off %ds + fresh session",
                                     attempt, doi, self.HTML_RETRY_SLEEP)
                    self._reset_session()
                    time.sleep(self.HTML_RETRY_SLEEP)
                    continue
                raise RuntimeError(last_err)
        raise RuntimeError(last_err or "unknown")

    def _download_pdf(self, arnum: str, job: Job) -> Path:
        s = self._session
        s.get(f"https://ieeexplore.ieee.org/document/{arnum}/", timeout=60)
        stamp_url = f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={arnum}"
        s.get(stamp_url, timeout=60,
              headers={"Referer": f"https://ieeexplore.ieee.org/document/{arnum}/"})
        pdf_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnum}&ref="
        r3 = s.get(pdf_url, timeout=180, allow_redirects=True,
                   headers={"Referer": stamp_url})

        ct = r3.headers.get("Content-Type", "")
        if "pdf" not in ct.lower() or r3.content[:4] != b"%PDF":
            if "APM_DO_NOT_TOUCH" in r3.text[:400]:
                raise _AkamaiChallenge(
                    f"APM HTML (status={r3.status_code}, ct={ct!r})"
                )
            snippet = r3.text[:300] if hasattr(r3, "text") else str(r3.content[:300])
            raise RuntimeError(f"not a PDF (status={r3.status_code}, ct={ct!r}, "
                               f"head={snippet[:120]!r})")

        out_pdf = self.out_dir / job.safe_name
        out_pdf.write_bytes(r3.content)
        self.log.info("[ieee] saved -> %s (%d bytes)",
                      out_pdf.name, out_pdf.stat().st_size)
        return out_pdf

    def _reset_session(self) -> None:
        try:
            if self._session is not None:
                self._session.close()
        except Exception:
            pass
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
