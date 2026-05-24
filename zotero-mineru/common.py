"""Shared logic for Zotero PDF -> MD conversion via mineru."""
from __future__ import annotations

import contextlib
import filecmp
import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import warnings
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)
logging.getLogger("pypdf._reader").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", module="pypdf")


def zotero_trashed_status(key: str, config: dict) -> tuple[bool | None, str]:
    """Query Zotero local API to learn if attachment <key> is in trash.

    Returns (is_trashed, detail). is_trashed is None on transport error
    (caller should not treat as trashed in that case).
    """
    base = config.get("zotero_api_base", "http://localhost:23119")
    lib = config.get("zotero_library_id")
    if not lib:
        return None, "no zotero_library_id in config"
    url = f"{base}/api/users/{lib}/items/{key}?format=json"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "item not in Zotero DB"
        return None, f"HTTP {e.code}"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        return None, f"transport: {e}"
    return bool(d.get("data", {}).get("deleted")), "ok"


def get_pdf_page_count(pdf_path: Path) -> int | None:
    """Return PDF page count, or None if the file can't be parsed."""
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            reader = PdfReader(str(pdf_path), strict=False)
            return len(reader.pages)
    except Exception:
        return None


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_logging(log_dir: Path, name: str) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def load_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_file.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, state_file)


def scan_storage(storage_dir: Path) -> list[tuple[str, Path]]:
    """Yield (zotero_key, pdf_path) for every PDF under Zotero/storage/."""
    results: list[tuple[str, Path]] = []
    for entry in storage_dir.iterdir():
        if not entry.is_dir():
            continue
        key = entry.name
        for pdf in entry.glob("*.pdf"):
            results.append((key, pdf))
    return results


def pdf_fingerprint(pdf_path: Path) -> dict:
    st = pdf_path.stat()
    return {"mtime": st.st_mtime, "size": st.st_size}


def needs_conversion(key: str, pdf_path: Path, state: dict) -> bool:
    """True if this PDF should be (re)processed."""
    entry = state.get(key)
    if not entry:
        return True
    status = entry.get("status")
    fp = pdf_fingerprint(pdf_path)
    file_changed = (
        entry.get("pdf_mtime") != fp["mtime"]
        or entry.get("pdf_size") != fp["size"]
    )
    if file_changed:
        return True
    if status == "ok":
        # Already converted; only re-run if md output is missing.
        return not entry.get("md_path") or not Path(entry["md_path"]).exists()
    if status == "skipped_too_large":
        # Settled, do not retry unless max_pages config changed or file changed.
        return False
    if status == "skipped_trashed":
        # Re-evaluate every run; the user may have restored the item.
        return True
    # status == "failed" or unknown: let caller decide based on retry policy.
    return True


def find_produced_md(output_root: Path) -> Path | None:
    """Walk mineru's output dir for the produced .md file (largest one)."""
    candidates = list(output_root.rglob("*.md"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_size)


def convert_one(
    key: str,
    pdf_path: Path,
    config: dict,
    logger: logging.Logger,
) -> tuple[bool, str, Path | None]:
    """Run mineru on one PDF. Returns (ok, message, md_path)."""
    mineru = Path(config["mineru_exe"])
    if not mineru.exists():
        return False, f"mineru exe missing: {mineru}", None

    mirror_dir = Path(config["mirror_dir"])
    target_dir = mirror_dir / key
    # Run mineru into a temp dir, then move the relevant md into target_dir.
    target_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"mineru_{key}_") as tmpd:
        tmp_out = Path(tmpd)
        # Windows MAX_PATH (260 chars) workaround: mineru names its output
        # subdirectory using the input PDF's stem, so long Chinese / English
        # paper titles can push the path past the limit when writing image
        # files. Copy the PDF to a short-named alias before running mineru.
        short_pdf = tmp_out / f"{key}.pdf"
        shutil.copy2(pdf_path, short_pdf)
        cmd = [
            str(mineru),
            "-p", str(short_pdf),
            "-o", str(tmp_out),
            *config.get("mineru_extra_args", []),
        ]
        logger.info("[%s] running: %s", key, " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=config.get("convert_timeout_seconds", 1800),
            )
        except subprocess.TimeoutExpired:
            return False, "timeout", None
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "")[-2000:]
            return False, f"mineru exit {proc.returncode}: {tail}", None

        md = find_produced_md(tmp_out)
        if not md:
            return False, "no .md produced", None

        # Copy mineru's output (md + images + layout) into target_dir.
        # Mineru writes under tmp_out/<KEY>/ because we fed it <KEY>.pdf;
        # flatten that one level so target_dir/ holds hybrid_auto/, images, etc.
        for child in target_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        mineru_subdir = tmp_out / key
        copy_root = mineru_subdir if mineru_subdir.is_dir() else tmp_out
        for item in copy_root.iterdir():
            if item.resolve() == short_pdf.resolve():
                continue  # skip the short-named PDF alias we copied in
            dest = target_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # Re-locate the md inside target_dir.
        final_md = find_produced_md(target_dir)
        if not final_md:
            return False, "md vanished after copy", None
        return True, "ok", final_md


# ---------------------------------------------------------------------------
# Large-PDF support: split into page ranges, run mineru on each, merge
# (Logic adapted from mybooksystem/pdf_mineru_batch/{run_pipeline_local_auto_split,bigfile}.py)
# ---------------------------------------------------------------------------

def page_ranges(page_count: int, max_length: int) -> list[tuple[int, int]]:
    if max_length <= 0:
        raise ValueError("max_length must be > 0")
    ranges: list[tuple[int, int]] = []
    for start in range(0, page_count, max_length):
        end = min(start + max_length - 1, page_count - 1)
        ranges.append((start, end))
    return ranges


def _find_part_md(part_dir: Path, name: str) -> Path | None:
    """Mineru may put output under <part>/<name>/hybrid_auto/<name>.md (or a few
    variants). Probe known locations."""
    candidates = [
        part_dir / name / "hybrid_auto",
        part_dir / name,
        part_dir / "hybrid_auto",
        part_dir,
    ]
    for c in candidates:
        f = c / f"{name}.md"
        if f.exists():
            return f
    # Fallback: any .md anywhere
    found = list(part_dir.rglob("*.md"))
    return max(found, key=lambda p: p.stat().st_size) if found else None


def _merge_parts(part_md_files: list[Path], target_dir: Path, name: str, logger) -> Path | None:
    """Merge a list of per-part MDs (in order) into target_dir/<name>.md,
    deduping images by name and rewriting image refs when collisions rename them."""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    images_root = target_dir / "images"
    images_root.mkdir(parents=True, exist_ok=True)

    merged_sections: list[str] = []
    for i, md_file in enumerate(part_md_files, start=1):
        try:
            md_text = md_file.read_text(encoding="utf-8-sig")
        except OSError as e:
            logger.warning("part %d: read failed %s: %s", i, md_file, e)
            continue
        images_dir = md_file.parent / "images"
        if images_dir.is_dir():
            for img in images_dir.iterdir():
                if not img.is_file():
                    continue
                target_name = img.name
                target_path = images_root / target_name
                if target_path.exists() and not filecmp.cmp(img, target_path, shallow=False):
                    target_name = f"p{i:02d}_{img.name}"
                    target_path = images_root / target_name
                shutil.copy2(img, target_path)
                if target_name != img.name:
                    md_text = md_text.replace(f"images/{img.name}", f"images/{target_name}")
                    md_text = md_text.replace(f"images\\{img.name}", f"images\\{target_name}")
        if md_text.strip():
            merged_sections.append(md_text.strip())
        logger.info("merged part %d: %s (md=%d chars)", i, md_file.name, len(md_text))

    merged_md = target_dir / f"{name}.md"
    merged_md.write_text("\n\n".join(merged_sections) + "\n", encoding="utf-8")
    return merged_md if merged_md.exists() else None


def convert_large_pdf(
    key: str,
    pdf_path: Path,
    config: dict,
    page_count: int,
    logger: logging.Logger,
) -> tuple[bool, str, Path | None]:
    """Run mineru in page-range chunks, then merge the parts into one MD folder.
    Returns (ok, message, md_path)."""
    mineru = Path(config["mineru_exe"])
    if not mineru.exists():
        return False, f"mineru exe missing: {mineru}", None

    mirror_dir = Path(config["mirror_dir"])
    target_dir = mirror_dir / key

    split_pages = int(config.get("split_chunk_pages", 200))
    ranges = page_ranges(page_count, split_pages)
    logger.info("[%s] LARGE (%d pages): splitting into %d part(s) of <= %d pages",
                key, page_count, len(ranges), split_pages)

    with tempfile.TemporaryDirectory(prefix=f"mineru_large_{key}_") as tmpd:
        tmp_root = Path(tmpd)
        # Same short-name trick to avoid Windows MAX_PATH problems.
        short_pdf = tmp_root / f"{key}.pdf"
        shutil.copy2(pdf_path, short_pdf)

        part_md_files: list[Path] = []
        for i, (start, end) in enumerate(ranges, start=1):
            part_dir = tmp_root / f"part_{i:03d}"
            part_dir.mkdir(parents=True, exist_ok=True)
            cmd = [
                str(mineru),
                "-p", str(short_pdf),
                "-o", str(part_dir),
                "--start", str(start),
                "--end", str(end),
                *config.get("mineru_extra_args", []),
            ]
            logger.info("[%s] part %d/%d pages %d-%d", key, i, len(ranges), start, end)
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=config.get("convert_timeout_seconds", 1800),
                )
            except subprocess.TimeoutExpired:
                return False, f"part {i} timeout (pages {start}-{end})", None
            if proc.returncode != 0:
                tail = (proc.stderr or proc.stdout or "")[-2000:]
                return False, f"part {i} mineru exit {proc.returncode}: {tail}", None
            md = _find_part_md(part_dir, key)
            if not md:
                return False, f"part {i}: no md produced", None
            part_md_files.append(md)

        merged = _merge_parts(part_md_files, target_dir, key, logger)
        if not merged:
            return False, "merge produced no md", None
        return True, f"ok-split-{len(ranges)}parts", merged


def process_pdf(
    key: str,
    pdf_path: Path,
    config: dict,
    state: dict,
    logger: logging.Logger,
    state_file: Path,
) -> bool:
    """Convert one PDF if needed; update state on disk. Returns True if converted, False if skipped."""
    if not needs_conversion(key, pdf_path, state):
        return False

    entry = state.get(key, {})
    attempts = int(entry.get("attempts", 0))
    max_retries = int(config.get("max_retries", 3))
    if entry.get("status") == "failed" and attempts >= max_retries:
        logger.info("[%s] skipping (failed %d times)", key, attempts)
        return False

    try:
        fp = pdf_fingerprint(pdf_path)
    except FileNotFoundError:
        # Zotero may relocate/rename a PDF mid-import; the file we scanned
        # at the top of the run no longer exists. Skip without crashing.
        logger.warning("[%s] PDF vanished between scan and process: %s", key, pdf_path)
        state[key] = {
            "pdf_path": str(pdf_path),
            "status": "vanished",
            "md_path": None,
            "attempts": 0,
            "last_error": "file not found at process time",
            "last_run": datetime.now().isoformat(timespec="seconds"),
        }
        save_state(state_file, state)
        return False

    # Trash gate: skip items currently in Zotero's Trash. Transport errors do
    # NOT mark the item as trashed — we proceed to conversion in that case.
    if config.get("skip_trashed", True):
        trashed, detail = zotero_trashed_status(key, config)
        if trashed is True:
            logger.info("[%s] SKIP (in Zotero Trash): %s", key, pdf_path.name)
            state[key] = {
                "pdf_path": str(pdf_path),
                "pdf_mtime": fp["mtime"],
                "pdf_size": fp["size"],
                "status": "skipped_trashed",
                "md_path": None,
                "attempts": 0,
                "last_error": None,
                "last_run": datetime.now().isoformat(timespec="seconds"),
            }
            save_state(state_file, state)
            return False
        if trashed is None and detail != "ok":
            logger.warning("[%s] trash check failed (%s); proceeding anyway", key, detail)

    # Page-count gate.
    max_pages = int(config.get("max_pages", 0))
    page_count = get_pdf_page_count(pdf_path)
    is_large = max_pages > 0 and page_count is not None and page_count > max_pages
    process_large = bool(config.get("process_large", False))

    if is_large and not process_large:
        logger.info("[%s] SKIP %d-page PDF (limit %d): %s", key, page_count, max_pages, pdf_path.name)
        state[key] = {
            "pdf_path": str(pdf_path),
            "pdf_mtime": fp["mtime"],
            "pdf_size": fp["size"],
            "page_count": page_count,
            "status": "skipped_too_large",
            "md_path": None,
            "attempts": 0,
            "last_error": None,
            "last_run": datetime.now().isoformat(timespec="seconds"),
        }
        save_state(state_file, state)
        return False

    t0 = time.time()
    if is_large:
        logger.info("[%s] converting LARGE %s (%d pages, split-mode)", key, pdf_path.name, page_count)
        ok, msg, md_path = convert_large_pdf(key, pdf_path, config, page_count, logger)
    else:
        logger.info("[%s] converting %s (%s pages)", key, pdf_path.name, page_count if page_count is not None else "?")
        ok, msg, md_path = convert_one(key, pdf_path, config, logger)
    elapsed = time.time() - t0

    entry = {
        "pdf_path": str(pdf_path),
        "pdf_mtime": fp["mtime"],
        "pdf_size": fp["size"],
        "last_run": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round(elapsed, 1),
    }
    if page_count is not None:
        entry["page_count"] = page_count
    if ok and md_path is not None:
        entry.update({
            "status": "ok",
            "md_path": str(md_path),
            "attempts": 0,
            "last_error": None,
        })
        logger.info("[%s] OK in %.1fs -> %s", key, elapsed, md_path)
    else:
        entry.update({
            "status": "failed",
            "md_path": None,
            "attempts": attempts + 1,
            "last_error": msg,
        })
        logger.error("[%s] FAILED (%s)", key, msg)

    state[key] = entry
    save_state(state_file, state)
    return ok
