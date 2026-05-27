"""Daemon: watch Zotero storage and refresh index/cleanup derived outputs.

Set watcher_auto_convert=true in config.json only if you explicitly want the
watcher to run MinerU. The default local config keeps conversion manual via
batch.py/run-batch.ps1.
"""
from __future__ import annotations

import argparse
import queue
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from common import (
    cleanup_deleted_outputs,
    load_config,
    load_state,
    needs_conversion,
    process_pdf,
    rebuild_index,
    scan_storage,
    setup_logging,
    start_mineru_api,
    stop_mineru_api,
)


class PdfEventHandler(FileSystemEventHandler):
    def __init__(self, work_queue: queue.Queue, storage: Path, logger):
        self.queue = work_queue
        self.storage = storage
        self.logger = logger

    def _key_for_path(self, path_str: str) -> tuple[str, Path] | None:
        path = Path(path_str)
        if path.suffix.lower() != ".pdf":
            return None
        try:
            rel = path.relative_to(self.storage)
        except ValueError:
            return None
        # Zotero stores PDFs at storage/<KEY>/file.pdf — exactly two parts.
        if len(rel.parts) < 2:
            return None
        key = rel.parts[0]
        return key, path

    def _maybe_enqueue_process(self, path_str: str) -> None:
        found = self._key_for_path(path_str)
        if not found:
            return
        key, path = found
        self.logger.info("event: %s -> queue key=%s", path.name, key)
        self.queue.put(("process", key, path))

    def _maybe_enqueue_delete(self, path_str: str) -> None:
        found = self._key_for_path(path_str)
        if not found:
            return
        key, path = found
        self.logger.info("delete event: %s -> cleanup key=%s", path.name, key)
        self.queue.put(("delete", key, path))

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_enqueue_process(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_enqueue_process(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_enqueue_delete(event.src_path)
            self._maybe_enqueue_process(event.dest_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_enqueue_delete(event.src_path)


def wait_until_stable(pdf_path: Path, stable_seconds: int, logger) -> bool:
    """Wait until the PDF size stops changing for stable_seconds. Returns False if it vanished."""
    last_size = -1
    last_change = time.time()
    while True:
        if not pdf_path.exists():
            logger.warning("file vanished while waiting: %s", pdf_path)
            return False
        size = pdf_path.stat().st_size
        if size != last_size:
            last_size = size
            last_change = time.time()
        elif time.time() - last_change >= stable_seconds:
            return True
        time.sleep(1)


def worker_loop(work_queue: queue.Queue, config: dict, logger, state_file: Path) -> None:
    state = load_state(state_file)
    seen_recent: dict[tuple[str, str], float] = {}
    stable_seconds = int(config.get("stable_seconds", 10))
    debounce_seconds = 5
    sync_interval = int(config.get("sync_interval_seconds", 300))
    auto_convert = bool(config.get("watcher_auto_convert", True))
    index_dirty = False

    while True:
        try:
            action, key, pdf_path = work_queue.get(timeout=sync_interval)
        except queue.Empty:
            state = load_state(state_file)
            removed = cleanup_deleted_outputs(config, state, logger, state_file, check_zotero=True)
            if removed:
                rebuild_index(config, logger)
            continue

        try:
            if action == "rebuild":
                if index_dirty or key == "force":
                    rebuild_index(config, logger)
                    index_dirty = False
                continue

            if action == "delete":
                state = load_state(state_file)
                cleanup_deleted_outputs(
                    config,
                    state,
                    logger,
                    state_file,
                    keys=[key],
                    check_zotero=True,
                    clean_orphan_mirror=False,
                )
                index_dirty = True
                continue

            # Debounce: collapse rapid-fire events for same path.
            now = time.time()
            sig = (key, str(pdf_path))
            if now - seen_recent.get(sig, 0) < debounce_seconds:
                continue
            seen_recent[sig] = now

            if not pdf_path or not pdf_path.exists():
                state = load_state(state_file)
                cleanup_deleted_outputs(
                    config,
                    state,
                    logger,
                    state_file,
                    keys=[key],
                    check_zotero=True,
                    clean_orphan_mirror=False,
                )
                index_dirty = True
                continue
            if not wait_until_stable(pdf_path, stable_seconds, logger):
                state = load_state(state_file)
                cleanup_deleted_outputs(
                    config,
                    state,
                    logger,
                    state_file,
                    keys=[key],
                    check_zotero=True,
                    clean_orphan_mirror=False,
                )
                index_dirty = True
                continue

            # Reload state in case batch.py also ran.
            state = load_state(state_file)
            if not auto_convert:
                logger.info("[%s] PDF changed; watcher_auto_convert=false, rebuilding index only", key)
                index_dirty = True
                continue
            if not needs_conversion(key, pdf_path, state):
                logger.info("[%s] already up-to-date, skipping", key)
                continue
            process_pdf(key, pdf_path, config, state, logger, state_file)
            index_dirty = True
        except Exception:
            logger.exception("worker error on %s", pdf_path)
        finally:
            if index_dirty and work_queue.empty():
                rebuild_index(config, logger)
                index_dirty = False
            work_queue.task_done()


def initial_sweep(work_queue: queue.Queue, storage: Path, state_file: Path, logger, config: dict) -> int:
    if not config.get("watcher_auto_convert", True):
        logger.info("initial sweep: watcher_auto_convert=false; rebuilding index without converting PDFs")
        work_queue.put(("rebuild", "force", None))
        return 0

    state = load_state(state_file)
    pending = [(k, p) for k, p in scan_storage(storage) if needs_conversion(k, p, state)]
    logger.info("initial sweep: %d PDFs need conversion", len(pending))
    for k, p in pending:
        work_queue.put(("process", k, p))
    return len(pending)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
    parser.add_argument("--no-initial-sweep", action="store_true", help="Skip scanning existing PDFs at startup.")
    parser.add_argument("--force", action="store_true", help="Run watcher even when watcher_enabled is false.")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    log_dir = Path(config["log_dir"])
    logger = setup_logging(log_dir, "watcher")

    if not args.force and not config.get("watcher_enabled", False):
        logger.info("watcher is disabled in config.json; use batch.py/run-batch.ps1 for manual sync")
        print("watcher is disabled in config.json; run .\\run-batch.ps1 for manual sync")
        return 0

    storage = Path(config["zotero_storage"])
    state_file = Path(config["state_file"])

    # Start mineru-api if configured (stays running for the watcher's lifetime).
    api_proc = start_mineru_api(config, logger)

    work_queue: queue.Queue = queue.Queue()

    state = load_state(state_file)
    startup_removed = cleanup_deleted_outputs(config, state, logger, state_file, check_zotero=True)

    if not args.no_initial_sweep:
        initial_sweep(work_queue, storage, state_file, logger, config)

    if startup_removed:
        work_queue.put(("rebuild", "force", None))

    worker = threading.Thread(
        target=worker_loop,
        args=(work_queue, config, logger, state_file),
        daemon=True,
        name="watcher-worker",
    )
    worker.start()

    handler = PdfEventHandler(work_queue, storage, logger)
    observer = Observer()
    observer.schedule(handler, str(storage), recursive=True)
    observer.start()
    logger.info("watching %s", storage)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("shutting down")
        observer.stop()
    observer.join()
    stop_mineru_api(api_proc, logger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
