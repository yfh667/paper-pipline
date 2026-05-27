"""Shared logic for Zotero PDF -> MD conversion via mineru."""
from __future__ import annotations

import contextlib
import filecmp
import io
import json
import logging
import os
import re
import signal
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

from pypdf import PdfReader, PdfWriter

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


_ZOTERO_KEY_RE = re.compile(r"^[A-Z0-9]{8}$", re.IGNORECASE)


def index_file_from_config(config: dict) -> Path:
    """Return the configured index path, defaulting to mirror_dir/index.json."""
    if config.get("index_file"):
        return Path(config["index_file"])
    return Path(config["mirror_dir"]) / "index.json"


def _safe_remove_tree(root: Path, target: Path, logger: logging.Logger) -> bool:
    """Remove target only if it resolves inside root."""
    root_resolved = root.resolve(strict=False)
    target_resolved = target.resolve(strict=False)
    try:
        target_resolved.relative_to(root_resolved)
    except ValueError:
        logger.warning("refusing to remove path outside mirror_dir: %s", target_resolved)
        return False
    if target_resolved == root_resolved:
        logger.warning("refusing to remove mirror_dir itself: %s", target_resolved)
        return False
    if not target_resolved.exists():
        return False
    shutil.rmtree(target_resolved)
    logger.info("removed mirror output: %s", target_resolved)
    return True


def remove_outputs_for_key(
    key: str,
    config: dict,
    state: dict | None,
    logger: logging.Logger,
) -> bool:
    """Remove state entry and converted mirror output for one Zotero attachment key."""
    changed = False
    if state is not None and key in state:
        state.pop(key, None)
        logger.info("[%s] removed from state.json", key)
        changed = True

    if config.get("remove_mirror_on_delete", True):
        mirror_dir = Path(config["mirror_dir"])
        changed = _safe_remove_tree(mirror_dir, mirror_dir / key, logger) or changed
    return changed


def scan_storage_by_key(storage_dir: Path) -> dict[str, list[Path]]:
    """Return current Zotero storage PDFs grouped by attachment key."""
    out: dict[str, list[Path]] = {}
    for key, pdf in scan_storage(storage_dir):
        out.setdefault(key, []).append(pdf)
    return out


def cleanup_deleted_outputs(
    config: dict,
    state: dict,
    logger: logging.Logger,
    state_file: Path | None = None,
    keys: set[str] | list[str] | tuple[str, ...] | None = None,
    check_zotero: bool | None = None,
    clean_orphan_mirror: bool = True,
) -> list[str]:
    """Delete state/mirror outputs for PDFs no longer live in Zotero.

    This is intentionally conservative: Zotero API transport errors do not
    delete anything. Physical absence from Zotero/storage does.
    """
    if not config.get("cleanup_deleted", True):
        return []

    storage = Path(config["zotero_storage"])
    live_by_key = scan_storage_by_key(storage) if storage.exists() else {}
    target_keys = {k for k in (keys or state.keys()) if k}

    if keys is None and clean_orphan_mirror:
        mirror_dir = Path(config["mirror_dir"])
        if mirror_dir.exists():
            for sub in mirror_dir.iterdir():
                if sub.is_dir() and _ZOTERO_KEY_RE.match(sub.name):
                    target_keys.add(sub.name)

    do_zotero_check = config.get("cleanup_check_zotero", True) if check_zotero is None else check_zotero
    removed: list[str] = []
    state_changed = False
    api_transport_errors = 0

    for key in sorted(target_keys):
        reason: str | None = None
        live_pdfs = live_by_key.get(key, [])
        if not live_pdfs:
            reason = "no PDF remains in Zotero storage"
        elif do_zotero_check and config.get("skip_trashed", True):
            if api_transport_errors < 3:
                trashed, detail = zotero_trashed_status(key, config)
                if trashed is True:
                    reason = "item is in Zotero trash"
                elif detail == "item not in Zotero DB":
                    reason = detail
                elif trashed is None and detail.startswith("transport"):
                    api_transport_errors += 1
                    if api_transport_errors == 3:
                        logger.warning("stopping Zotero cleanup checks after 3 API transport errors")

        if not reason:
            continue

        had_state = key in state
        if remove_outputs_for_key(key, config, state, logger):
            logger.info("[%s] cleaned deleted output (%s)", key, reason)
            removed.append(key)
        if had_state:
            state_changed = True

    if state_changed and state_file is not None:
        save_state(state_file, state)
    return removed


def rebuild_index(config: dict, logger: logging.Logger) -> bool:
    """Rebuild index.json using the current Python executable."""
    if not config.get("rebuild_index_on_change", True):
        return False

    script = Path(__file__).with_name("build_index.py")
    state_file = Path(config["state_file"])
    index_file = index_file_from_config(config)
    cmd = [
        sys.executable,
        str(script),
        "--state", str(state_file),
        "--out", str(index_file),
        "--api-base", str(config.get("zotero_api_base", "http://localhost:23119")),
        "--library-id", str(config.get("zotero_library_id", "")),
    ]
    logger.info("rebuilding index: %s", index_file)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=config.get("index_rebuild_timeout_seconds", 900),
        )
    except subprocess.TimeoutExpired:
        logger.error("index rebuild timed out: %s", index_file)
        return False

    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    tail = output.strip()[-4000:]
    if proc.returncode != 0:
        logger.error("index rebuild failed with exit %d:\n%s", proc.returncode, tail)
        return False
    if tail:
        logger.info("index rebuild output:\n%s", tail)
    logger.info("index rebuilt: %s", index_file)
    return True


# ---------------------------------------------------------------------------
# mineru-api lifecycle management
# ---------------------------------------------------------------------------

def _api_base_url(config: dict) -> str:
    host = config.get("api_host", "127.0.0.1")
    port = config.get("api_port", 8000)
    return f"http://{host}:{port}"


def _api_healthy(config: dict) -> bool:
    url = _api_base_url(config) + "/health"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def start_mineru_api(config: dict, logger: logging.Logger) -> subprocess.Popen | None:
    if not config.get("use_api", False):
        return None

    if _api_healthy(config):
        logger.info("[api] existing mineru-api is healthy: %s", _api_base_url(config))
        return None

    api_exe = Path(config.get("mineru_api_exe", ""))
    if not api_exe.exists():
        logger.warning("[api] mineru-api exe not found: %s; falling back to legacy mode", api_exe)
        config["use_api"] = False
        return None

    host = config.get("api_host", "127.0.0.1")
    port = str(config.get("api_port", 8000))

    env = os.environ.copy()
    env["MINERU_API_MAX_CONCURRENT_REQUESTS"] = str(config.get("api_concurrency", 4))
    env["MINERU_PDF_RENDER_THREADS"] = str(config.get("api_render_threads", 16))
    env["MINERU_PROCESSING_WINDOW_SIZE"] = str(config.get("api_processing_window_size", 32))

    cmd = [str(api_exe), "--host", host, "--port", port]
    if config.get("api_preload", True):
        cmd += ["--enable-vlm-preload", "true"]

    log_dir = Path(config.get("log_dir", "."))
    log_dir.mkdir(parents=True, exist_ok=True)
    api_log = log_dir / "mineru-api.log"

    logger.info("[api] starting: %s", " ".join(cmd))
    log_file = api_log.open("a", encoding="utf-8", buffering=1)
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        shell=False,
        creationflags=creationflags,
    )

    deadline = time.time() + config.get("api_start_timeout_seconds", 300)
    while time.time() < deadline:
        if _api_healthy(config):
            logger.info("[api] ready: %s (pid=%d)", _api_base_url(config), proc.pid)
            return proc
        if proc.poll() is not None:
            logger.error("[api] mineru-api exited during startup (rc=%d)", proc.returncode)
            config["use_api"] = False
            return None
        time.sleep(2)

    logger.error("[api] mineru-api did not become healthy in time; falling back to legacy")
    stop_mineru_api(proc, logger)
    config["use_api"] = False
    return None


def stop_mineru_api(proc: subprocess.Popen | None, logger: logging.Logger) -> None:
    if proc is None:
        return
    if proc.poll() is not None:
        return
    logger.info("[api] stopping mineru-api (pid=%d)", proc.pid)
    try:
        if os.name == "nt":
            proc.send_signal(signal.CTRL_BREAK_EVENT)
            try:
                proc.wait(timeout=10)
                return
            except subprocess.TimeoutExpired:
                proc.terminate()
        else:
            proc.terminate()
        proc.wait(timeout=20)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


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
        if config.get("use_api") and _api_healthy(config):
            cmd.extend(["--api-url", _api_base_url(config)])
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


def _split_pdf_physically(pdf_path: Path, chunk_pages: int, out_dir: Path,
                          logger: logging.Logger) -> list[Path]:
    """Split a PDF into chunk_pages-sized files. Returns list of chunk paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with contextlib.redirect_stderr(io.StringIO()):
        reader = PdfReader(str(pdf_path), strict=False)
    total = len(reader.pages)
    chunks: list[Path] = []
    for idx, start in enumerate(range(0, total, chunk_pages), 1):
        end = min(start + chunk_pages, total)
        chunk_path = out_dir / f"chunk_{idx:03d}_p{start+1:04d}-{end:04d}.pdf"
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])
        with chunk_path.open("wb") as f:
            writer.write(f)
        logger.info("  split chunk %d: pages %d-%d (%d pages)", idx, start + 1, end, end - start)
        chunks.append(chunk_path)
    return chunks


def convert_large_pdf(
    key: str,
    pdf_path: Path,
    config: dict,
    page_count: int,
    logger: logging.Logger,
) -> tuple[bool, str, Path | None]:
    """Split PDF into small chunks, run mineru on each (via API if available),
    then merge the parts into one MD folder. Returns (ok, message, md_path)."""
    mineru = Path(config["mineru_exe"])
    if not mineru.exists():
        return False, f"mineru exe missing: {mineru}", None

    mirror_dir = Path(config["mirror_dir"])
    target_dir = mirror_dir / key

    split_pages = int(config.get("split_chunk_pages", 40))
    logger.info("[%s] LARGE (%d pages): physically splitting into %d-page chunks",
                key, page_count, split_pages)

    use_api = config.get("use_api") and _api_healthy(config)
    api_url_args = ["--api-url", _api_base_url(config)] if use_api else []

    with tempfile.TemporaryDirectory(prefix=f"mineru_large_{key}_") as tmpd:
        tmp_root = Path(tmpd)
        chunks_dir = tmp_root / "chunks"
        chunk_files = _split_pdf_physically(pdf_path, split_pages, chunks_dir, logger)
        logger.info("[%s] split into %d chunk(s)", key, len(chunk_files))

        part_md_files: list[Path] = []
        for i, chunk_pdf in enumerate(chunk_files, start=1):
            part_dir = tmp_root / f"part_{i:03d}"
            part_dir.mkdir(parents=True, exist_ok=True)
            short_pdf = part_dir / f"{key}.pdf"
            shutil.copy2(chunk_pdf, short_pdf)
            cmd = [
                str(mineru),
                "-p", str(short_pdf),
                "-o", str(part_dir),
                *api_url_args,
                *config.get("mineru_extra_args", []),
            ]
            logger.info("[%s] part %d/%d (%s)", key, i, len(chunk_files), chunk_pdf.name)
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
                return False, f"part {i} timeout ({chunk_pdf.name})", None
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
        return True, f"ok-split-{len(chunk_files)}parts", merged


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
        # at the top of the run no longer exists. Remove stale outputs.
        logger.warning("[%s] PDF vanished between scan and process: %s", key, pdf_path)
        if remove_outputs_for_key(key, config, state, logger):
            save_state(state_file, state)
        return False

    # Trash gate: skip items currently in Zotero's Trash. Transport errors do
    # NOT mark the item as trashed — we proceed to conversion in that case.
    if config.get("skip_trashed", True):
        trashed, detail = zotero_trashed_status(key, config)
        if trashed is True:
            logger.info("[%s] CLEANUP (in Zotero Trash): %s", key, pdf_path.name)
            if remove_outputs_for_key(key, config, state, logger):
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
