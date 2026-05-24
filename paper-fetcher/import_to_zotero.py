"""Import output/{ieee,acm,sd}/*.pdf into the running local Zotero desktop.

Uses Zotero's local Connector endpoint POST /connector/saveStandaloneAttachment
to upload each PDF as a standalone attachment. Zotero then auto-recognizes the
PDF metadata (queries DOI.org / CrossRef from PDF text) and creates a proper
journalArticle parent with full bibliographic info.

The Web API on port 23119 is read-only for writes, so we cannot create
collections programmatically. Items land in "Unfiled Items" by default. To
group them into a "paper-fetcher" collection: open Zotero, multi-select the
new items in Unfiled, drag to your collection. (Files themselves live under
Zotero\\storage\\<key>\\ regardless of collection — your zotero-mineru
pipeline picks them up either way.)

Usage:
    python import_to_zotero.py                  # import all new PDFs
    python import_to_zotero.py --limit 1        # smoke test
    python import_to_zotero.py --dry-run        # list what would be uploaded
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
import uuid
from pathlib import Path

import requests

LIB_ID = 12146168
ZOTERO_BASE = "http://127.0.0.1:23119"
PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_DIRS = ["ieee", "acm", "sd"]
LOG_PATH = PROJECT_ROOT / "output" / "logs" / "zotero_import.log"

# /api endpoints on local Zotero only support GET, so we identify duplicates
# by MD5 (Zotero stores it on every imported attachment).


def setup_logger() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                            datefmt="%H:%M:%S")
    logger = logging.getLogger("zimport")
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler(sys.stdout); sh.setFormatter(fmt)
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8"); fh.setFormatter(fmt)
    logger.addHandler(sh); logger.addHandler(fh)
    return logger


def existing_md5s(log: logging.Logger) -> set[str]:
    """Pull md5 hashes of every imported-file/url attachment in the library so
    we can skip duplicates we've already pushed."""
    seen: set[str] = set()
    start = 0
    page = 100
    while True:
        try:
            r = requests.get(
                f"{ZOTERO_BASE}/api/users/{LIB_ID}/items",
                params={
                    "itemType": "attachment",
                    "format": "json",
                    "limit": page,
                    "start": start,
                },
                timeout=30,
            )
            r.raise_for_status()
        except Exception as e:
            log.warning("can't list existing attachments at start=%d: %s", start, e)
            break
        items = r.json()
        if not items:
            break
        for it in items:
            md5 = it.get("data", {}).get("md5")
            if md5:
                seen.add(md5)
        start += page
        # Total-Results header tells us when to stop
        total = int(r.headers.get("Total-Results", "0") or 0)
        if start >= total:
            break
    return seen


def upload_pdf(pdf: Path, log: logging.Logger) -> bool:
    """POST one PDF to Zotero's saveStandaloneAttachment endpoint."""
    session_id = uuid.uuid4().hex
    metadata = {
        "sessionID": session_id,
        "title": pdf.stem,
        "mimeType": "application/pdf",
        "url": f"file:///{pdf.as_posix()}",
    }
    try:
        with open(pdf, "rb") as f:
            data = f.read()
        r = requests.post(
            f"{ZOTERO_BASE}/connector/saveStandaloneAttachment",
            data=data,
            headers={
                "Content-Type": "application/pdf",
                "X-Zotero-Connector-API-Version": "3",
                "X-Metadata": json.dumps(metadata),
            },
            timeout=120,
        )
    except Exception as e:
        log.error("upload error %s: %s", pdf.name, e)
        return False
    if r.status_code != 201:
        log.error("upload non-201 %s: %d %s", pdf.name, r.status_code, r.text[:200])
        return False
    try:
        result = r.json() if r.text else {}
    except json.JSONDecodeError:
        result = {}
    can_recognize = result.get("canRecognize", False)
    log.info("uploaded: %s  (canRecognize=%s)", pdf.name, can_recognize)
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="cap number of PDFs to upload")
    ap.add_argument("--dry-run", action="store_true",
                    help="just list what would be uploaded")
    ap.add_argument("--no-dedupe", action="store_true",
                    help="don't skip PDFs whose MD5 is already in Zotero")
    ap.add_argument("--gap", type=float, default=2.0,
                    help="seconds to sleep between uploads (let Zotero settle)")
    args = ap.parse_args()

    log = setup_logger()
    log.info("Zotero local API: %s", ZOTERO_BASE)

    # Sanity check Zotero is reachable
    try:
        r = requests.get(f"{ZOTERO_BASE}/api/users/{LIB_ID}/collections?limit=1",
                         timeout=5)
        log.info("Zotero alive (HTTP %d, X-Zotero-Version=%s)",
                 r.status_code, r.headers.get("X-Zotero-Version", "?"))
    except Exception as e:
        log.error("Zotero local API not reachable: %s", e)
        return 2

    all_pdfs: list[Path] = []
    for d in SOURCE_DIRS:
        all_pdfs.extend((PROJECT_ROOT / "output" / d).glob("*.pdf"))
    all_pdfs.sort()
    log.info("%d PDFs in output dirs", len(all_pdfs))

    seen_md5: set[str] = set()
    if not args.no_dedupe:
        log.info("scanning existing Zotero attachments for dedup...")
        seen_md5 = existing_md5s(log)
        log.info("%d existing attachment md5s in library", len(seen_md5))

    todo: list[Path] = []
    skipped = 0
    for pdf in all_pdfs:
        if seen_md5:
            md5 = hashlib.md5(pdf.read_bytes()).hexdigest()
            if md5 in seen_md5:
                skipped += 1
                continue
        todo.append(pdf)

    if args.limit:
        todo = todo[: args.limit]

    log.info("queue: %d to upload, %d already-in-Zotero skipped", len(todo), skipped)

    if args.dry_run:
        for p in todo:
            log.info("[dry-run] would upload: %s", p.name)
        return 0

    ok = fail = 0
    for i, pdf in enumerate(todo, 1):
        log.info("(%d/%d) %s", i, len(todo), pdf.name)
        if upload_pdf(pdf, log):
            ok += 1
        else:
            fail += 1
        if i < len(todo):
            time.sleep(args.gap)

    log.info("==== %d ok, %d fail (of %d) ====", ok, fail, len(todo))
    log.info("PDFs land in Zotero 'Unfiled Items' by default. "
             "To group: select them in Zotero UI and drag to a collection.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
