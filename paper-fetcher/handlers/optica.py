"""Optica Publishing Group (opg.optica.org) — undetected-chromedriver to bypass Cloudflare Turnstile.

Flow:
  1. DOI -> doi.org -> opg.optica.org landing page (extract article URI like jocn-18-6-614)
  2. Navigate to /viewmedia.cfm?uri=<URI>&seq=0 (Turnstile challenge auto-solved by real Chrome)
  3. Chrome auto-downloads the PDF; watch tmp dir for it

URL patterns:
  Abstract: https://opg.optica.org/jocn/abstract.cfm?uri=jocn-18-6-614
  PDF:      https://opg.optica.org/viewmedia.cfm?uri=jocn-18-6-614&seq=0
  DOI:      10.1364/JOCN.586930  (prefix 10.1364/ is Optica)
"""
from __future__ import annotations

import asyncio
import re
import shutil
import time
from pathlib import Path

import undetected_chromedriver as uc

from .base import Job, PublisherHandler

TMP_DL = Path(__file__).resolve().parent.parent / "output" / "_optica_dl_tmp"


class _TurnstileStuck(Exception):
    pass


class OpticaHandler(PublisherHandler):
    tag = "optica"
    gap_seconds = 60
    TURNSTILE_WAIT_SEC = 60
    DOWNLOAD_TIMEOUT = 120
    RETRY_BACKOFF_SEC = 90
    MAX_ATTEMPTS = 2

    def __init__(self, *, out_dir: Path, logger):
        super().__init__(out_dir=out_dir, logger=logger)
        TMP_DL.mkdir(parents=True, exist_ok=True)
        self._driver: uc.Chrome | None = None
        self._lock = asyncio.Lock()

    async def setup(self) -> None:
        await asyncio.to_thread(self._launch_driver)
        self.log.info("[optica] chrome driver ready")

    async def teardown(self) -> None:
        if self._driver is not None:
            await asyncio.to_thread(self._quit_driver)

    def _launch_driver(self) -> None:
        opts = uc.ChromeOptions()
        opts.add_argument("--window-size=1280,900")
        opts.add_experimental_option("prefs", {
            "download.default_directory": str(TMP_DL),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.popups": 0,
        })
        self._driver = uc.Chrome(options=opts, version_main=148)

    def _quit_driver(self) -> None:
        try:
            self._driver.quit()  # type: ignore[union-attr]
        except Exception:
            pass
        self._driver = None

    async def fetch_one(self, job: Job) -> Path:
        async with self._lock:
            return await asyncio.to_thread(self._fetch_sync, job)

    def _fetch_sync(self, job: Job) -> Path:
        last_err: str | None = None
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                return self._download_once(job, attempt)
            except _TurnstileStuck as e:
                last_err = str(e)
                if attempt < self.MAX_ATTEMPTS:
                    self.log.warning("[optica] %s — back off %ds + restart driver",
                                     e, self.RETRY_BACKOFF_SEC)
                    self._restart_driver()
                    time.sleep(self.RETRY_BACKOFF_SEC)
                    continue
        raise RuntimeError(last_err or "unknown")

    def _extract_uri(self, doi: str) -> str:
        """Resolve DOI and extract Optica article URI (e.g. jocn-18-6-614)."""
        assert self._driver is not None
        drv = self._driver

        drv.get(f"https://doi.org/{doi}")
        self._wait_turnstile(drv)

        url = drv.current_url
        # Try URI from URL query param
        m = re.search(r"uri=([^&\s]+)", url)
        if m:
            return m.group(1)
        # Try from abstract URL path pattern
        m2 = re.search(r"/abstract\.cfm\?uri=(.+?)(?:&|$)", url)
        if m2:
            return m2.group(1)
        # Try from page source
        src = drv.page_source
        m3 = re.search(r'viewmedia\.cfm\?uri=([^&"]+)', src)
        if m3:
            return m3.group(1)
        raise RuntimeError(f"could not extract Optica URI from {url}")

    def _wait_turnstile(self, drv) -> None:
        """Wait for Cloudflare Turnstile / page load to complete."""
        for _ in range(self.TURNSTILE_WAIT_SEC):
            time.sleep(1)
            title = drv.title.lower()
            if "please wait" not in title and "just a moment" not in title:
                if "opg" in drv.current_url.lower() or "optica" in drv.current_url.lower():
                    return
        if "please wait" in drv.title.lower() or "just a moment" in drv.title.lower():
            raise _TurnstileStuck(f"turnstile stuck (title={drv.title!r})")

    def _download_once(self, job: Job, attempt: int) -> Path:
        assert self._driver is not None
        drv = self._driver
        self._clear_tmp()

        uri = self._extract_uri(job.doi)
        self.log.info("[optica] doi=%s -> uri=%s", job.doi, uri)

        # Navigate to PDF download URL
        pdf_url = f"https://opg.optica.org/viewmedia.cfm?uri={uri}&seq=0"
        try:
            drv.get(pdf_url)
        except Exception as e:
            if "ERR_ABORTED" not in str(e):
                self.log.warning("[optica] pdf nav: %s", e)

        # Wait for Turnstile on the PDF page too
        time.sleep(3)
        # Check if we got redirected to a challenge page
        if "please wait" in drv.title.lower():
            self.log.info("[optica] turnstile on PDF page, waiting...")
            self._wait_turnstile(drv)
            # After turnstile, the PDF should auto-download or we need to re-navigate
            time.sleep(5)

        saved = self._wait_for_download(timeout=self.DOWNLOAD_TIMEOUT)
        if saved is None:
            # Fallback: try the &r=1 redirect variant
            fallback_url = f"https://opg.optica.org/viewmedia.cfm?r=1&uri={uri}&seq=0"
            self.log.info("[optica] retrying with r=1: %s", fallback_url)
            try:
                drv.get(fallback_url)
            except Exception:
                pass
            time.sleep(5)
            saved = self._wait_for_download(timeout=self.DOWNLOAD_TIMEOUT)

        if saved is None:
            raise _TurnstileStuck(
                f"download timeout on attempt {attempt} for {job.doi}"
            )

        final_path = self.out_dir / job.safe_name
        if final_path.exists():
            final_path = self.out_dir / (
                final_path.stem + f"_{job.doi.replace('/', '_')}.pdf"
            )
        shutil.move(str(saved), str(final_path))
        self.log.info("[optica] saved -> %s (%d bytes)",
                      final_path.name, final_path.stat().st_size)
        return final_path

    def _restart_driver(self) -> None:
        self._quit_driver()
        time.sleep(2)
        self._launch_driver()

    @staticmethod
    def _clear_tmp() -> None:
        for f in TMP_DL.glob("*"):
            try:
                f.unlink()
            except Exception:
                pass

    @staticmethod
    def _wait_for_download(timeout: int = 90) -> Path | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(1)
            pdfs = list(TMP_DL.glob("*.pdf"))
            partials = list(TMP_DL.glob("*.crdownload"))
            if pdfs and not partials:
                return pdfs[0]
        return None
