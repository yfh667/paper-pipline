"""Elsevier / ScienceDirect — subprocess the Node fetcher.

SD's WAF flags Playwright + playwright-stealth (Python) but accepts
puppeteer-extra-plugin-stealth (Node). Rather than maintain a Python stealth
implementation, this handler shells out to ../sd-fetch-node/fetch-one.mjs,
which is the proven-working Node script.

The Node script:
  - Opens https://doi.org/<doi>
  - Waits for SD's lazy-loaded full-text sections to appear
  - Bails out on WAF / paywall text
  - Strips popovers, sticky access bar, Reading-Assistant widget
  - Prints to PDF (no print-media emulation — that would strip body)
"""
from __future__ import annotations

import asyncio
import os
import subprocess
from pathlib import Path

from .base import Job, PublisherHandler

# Resolve relative to project root: paper-fetcher/handlers/elsevier.py -> ../sd-fetch-node/fetch-one.mjs
DEFAULT_NODE_SCRIPT = (
    Path(__file__).resolve().parent.parent / "sd-fetch-node" / "fetch-one.mjs"
)
NODE_SCRIPT = Path(os.environ.get("SD_NODE_SCRIPT", str(DEFAULT_NODE_SCRIPT)))


class ElsevierHandler(PublisherHandler):
    tag = "elsevier"
    gap_seconds = 60
    NODE_TIMEOUT = 300       # max seconds per article

    def __init__(self, *, out_dir: Path, logger):
        super().__init__(out_dir=out_dir, logger=logger)
        self.script = NODE_SCRIPT

    async def setup(self) -> None:
        if not self.script.exists():
            raise RuntimeError(f"Node fetch script missing: {self.script}")
        proc = await asyncio.create_subprocess_exec(
            "node", "--version",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"node not available: {out.decode(errors='replace')[:200]}")
        self.log.info("[elsevier] node %s ready, script: %s",
                      out.decode().strip(), self.script)

    async def teardown(self) -> None:
        return None

    async def fetch_one(self, job: Job) -> Path:
        url = f"https://doi.org/{job.doi}"
        out_pdf = self.out_dir / job.safe_name

        self.log.info("[elsevier] node-fetch %s -> %s", job.doi, out_pdf.name)
        proc = await asyncio.create_subprocess_exec(
            "node", str(self.script), url, str(out_pdf),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(self.script.parent),
        )
        try:
            stdout_bytes, _ = await asyncio.wait_for(
                proc.communicate(), timeout=self.NODE_TIMEOUT
            )
        except asyncio.TimeoutError:
            try: proc.kill()
            except Exception: pass
            raise RuntimeError(f"node fetch timed out after {self.NODE_TIMEOUT}s")

        text = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        if proc.returncode != 0:
            tail = text.splitlines()[-8:] if text else []
            raise RuntimeError(f"node exit {proc.returncode}: {' | '.join(tail)}")
        if not out_pdf.exists() or out_pdf.stat().st_size < 50_000:
            raise RuntimeError(f"output PDF missing/too small: {out_pdf} "
                               f"(size={out_pdf.stat().st_size if out_pdf.exists() else 0})")

        self.log.info("[elsevier] saved -> %s (%d bytes)",
                      out_pdf.name, out_pdf.stat().st_size)
        return out_pdf
