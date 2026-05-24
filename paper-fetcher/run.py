"""Paper fetcher — main entry point.

Usage:
    python run.py <list.txt>           # process the list
    python run.py <list.txt> --doi 10.1109/...  # single ad-hoc fetch, ignores list
    python run.py <list.txt> --skip-existing    # skip jobs whose output PDF already exists

The list file format (produced upstream by some cleaning step) is:
    [tag] Paper title  (doi=10.xxxx/yyyy)
    [tag] Paper title  (doi=)            # no DOI -> goes to needs_manual
    [other-tag] ...                       # not ieee/acm/elsevier -> goes to needs_manual

Tags handled by this fetcher:
    [ieee]     -> output/ieee/
    [acm]      -> output/acm/
    [elsevier] -> output/sd/

Everything else gets appended to output/manual/needs_manual.txt for the user
to handle by hand.

Three handlers run in parallel (different publishers), each handler's queue
serial with a per-publisher polite gap.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import re
import sys
import time
from collections import Counter
from pathlib import Path

# Allow `python run.py` from this directory to find sibling modules.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from core import run_jobs               # noqa: E402
from handlers import REGISTRY, Job      # noqa: E402

OUTPUT_ROOT = PROJECT_ROOT / "output"
OUT_DIRS = {
    "ieee": OUTPUT_ROOT / "ieee",
    "acm": OUTPUT_ROOT / "acm",
    "elsevier": OUTPUT_ROOT / "sd",
}
MANUAL_FILE = OUTPUT_ROOT / "manual" / "needs_manual.txt"
LOG_DIR = OUTPUT_ROOT / "logs"

CLEAN_LINE_RE = re.compile(r"^\[([\w\-]+)\]\s+(.+?)\s+\(doi=([^)]*)\)\s*$")


def setup_logger() -> tuple[logging.Logger, Path]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"run-{time.strftime('%Y%m%d-%H%M%S')}.log"
    logger = logging.getLogger("fetcher")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                            datefmt="%H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger, log_path


def parse_list(path: Path, logger: logging.Logger,
               skip_existing: bool) -> tuple[list[Job], list[str]]:
    """Returns (jobs_to_run, lines_to_write_to_needs_manual)."""
    jobs: list[Job] = []
    manual_lines: list[str] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        m = CLEAN_LINE_RE.match(raw)
        if not m:
            continue
        tag = m.group(1).strip()
        title = m.group(2).strip()
        doi = m.group(3).strip()

        if tag not in REGISTRY or not doi:
            manual_lines.append(raw)
            continue

        out_dir = OUT_DIRS[tag]
        job = Job(doi=doi, title=title, tag=tag, out_dir=out_dir)

        if skip_existing and (out_dir / job.safe_name).exists():
            logger.info("skip-existing: %s/%s", tag, job.safe_name)
            continue
        jobs.append(job)
    return jobs, manual_lines


def write_manual_list(lines: list[str], logger: logging.Logger) -> None:
    MANUAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANUAL_FILE.write_text("\n".join(lines) + "\n" if lines else "",
                           encoding="utf-8")
    logger.info("wrote %d entries to %s", len(lines), MANUAL_FILE)


async def amain(args: argparse.Namespace) -> int:
    logger, log_path = setup_logger()
    logger.info("project root: %s", PROJECT_ROOT)
    logger.info("log file: %s", log_path)

    for d in OUT_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)

    list_path = Path(args.list)
    if not list_path.exists():
        logger.error("list file not found: %s", list_path)
        return 2

    jobs, manual_lines = parse_list(list_path, logger, args.skip_existing)
    write_manual_list(manual_lines, logger)

    if not jobs:
        logger.info("no jobs to run for known publishers")
        return 0

    breakdown = Counter(j.tag for j in jobs)
    logger.info("dispatching %d job(s): %s",
                len(jobs), ", ".join(f"{t}={n}" for t, n in breakdown.items()))

    results = await run_jobs(jobs, logger)

    ok = sum(1 for r in results if r.ok)
    logger.info("==== %d/%d ok ====", ok, len(results))
    for r in results:
        if r.ok:
            logger.info("OK   %-10s %s  (%.1fs)",
                        r.job.tag, r.job.doi, r.seconds)
        else:
            logger.info("FAIL %-10s %s  (%.1fs)  %s",
                        r.job.tag, r.job.doi, r.seconds, r.error)
    return 0 if ok == len(results) else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("list", help="cleaned paper list (format: [tag] title  (doi=...))")
    ap.add_argument("--skip-existing", action="store_true",
                    help="skip jobs whose output PDF already exists")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(amain(args)))


if __name__ == "__main__":
    main()
