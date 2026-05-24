"""ACM Digital Library — undetected-chromedriver to bypass Cloudflare.

Flow:
  1. Open dl.acm.org/doi/<doi>, wait for Cloudflare to clear
  2. Navigate to dl.acm.org/doi/pdf/<doi> -> triggers download
  3. Watch a tmp dir for the PDF appearing, move to out_dir under title-based name
"""
from __future__ import annotations

import asyncio
import shutil
import time
from pathlib import Path

import undetected_chromedriver as uc

from .base import Job, PublisherHandler

TMP_DL = Path(__file__).resolve().parent.parent / "output" / "_acm_dl_tmp"


class _CloudflareStuck(Exception):
    """Transient: Cloudflare didn't clear or PDF didn't download. Retry."""


class AcmHandler(PublisherHandler):
    tag = "acm"
    gap_seconds = 60
    CLOUDFLARE_WAIT_SEC = 60
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
        self.log.info("[acm] chrome driver ready")

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
            except _CloudflareStuck as e:
                last_err = str(e)
                if attempt < self.MAX_ATTEMPTS:
                    self.log.warning("[acm] %s — back off %ds + restart driver",
                                     e, self.RETRY_BACKOFF_SEC)
                    self._restart_driver()
                    time.sleep(self.RETRY_BACKOFF_SEC)
                    continue
        raise RuntimeError(last_err or "unknown")

    def _download_once(self, job: Job, attempt: int) -> Path:
        assert self._driver is not None
        drv = self._driver
        doi = job.doi
        self._clear_tmp()

        drv.get(f"https://dl.acm.org/doi/{doi}")
        for _ in range(self.CLOUDFLARE_WAIT_SEC):
            time.sleep(1)
            if "Just a moment" not in drv.title and "acm" in drv.current_url.lower():
                break
        if "Just a moment" in drv.title:
            raise _CloudflareStuck(
                f"cloudflare stuck on attempt {attempt} (title={drv.title!r})"
            )

        try:
            drv.get(f"https://dl.acm.org/doi/pdf/{doi}")
        except Exception as e:
            if "ERR_ABORTED" not in str(e):
                self.log.warning("[acm] pdf nav: %s", e)

        saved = self._wait_for_download(timeout=self.DOWNLOAD_TIMEOUT)
        if saved is None:
            raise _CloudflareStuck(
                f"download timeout on attempt {attempt} (likely cloudflare on /pdf/)"
            )

        final_path = self.out_dir / job.safe_name
        if final_path.exists():
            final_path = self.out_dir / (
                final_path.stem + f"_{doi.replace('/', '_')}.pdf"
            )
        shutil.move(str(saved), str(final_path))
        self.log.info("[acm] saved -> %s (%d bytes)",
                      final_path.name, final_path.stat().st_size)
        return final_path

    def _restart_driver(self) -> None:
        self._quit_driver()
        time.sleep(2)
        self._launch_driver()

    @staticmethod
    def _clear_tmp() -> None:
        for f in TMP_DL.glob("*"):
            try: f.unlink()
            except Exception: pass

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
