"""Daemon: watch Zotero storage and convert new/updated PDFs to MD via mineru."""
from __future__ import annotations

import argparse
import queue
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from common import (
    load_config,
    load_state,
    needs_conversion,
    process_pdf,
    scan_storage,
    setup_logging,
)


class PdfEventHandler(FileSystemEventHandler):
    def __init__(self, work_queue: queue.Queue, storage: Path, logger):
        self.queue = work_queue
        self.storage = storage
        self.logger = logger

    def _maybe_enqueue(self, path_str: str) -> None:
        path = Path(path_str)
        if path.suffix.lower() != ".pdf":
            return
        try:
            rel = path.relative_to(self.storage)
        except ValueError:
            return
        # Zotero stores PDFs at storage/<KEY>/file.pdf — exactly two parts.
        if len(rel.parts) < 2:
            return
        key = rel.parts[0]
        self.logger.info("event: %s -> queue key=%s", path.name, key)
        self.queue.put((key, path))

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_enqueue(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_enqueue(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_enqueue(event.dest_path)


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

    while True:
        key, pdf_path = work_queue.get()
        try:
            # Debounce: collapse rapid-fire events for same path.
            now = time.time()
            sig = (key, str(pdf_path))
            if now - seen_recent.get(sig, 0) < debounce_seconds:
                continue
            seen_recent[sig] = now

            if not pdf_path.exists():
                continue
            if not wait_until_stable(pdf_path, stable_seconds, logger):
                continue

            # Reload state in case batch.py also ran.
            state = load_state(state_file)
            if not needs_conversion(key, pdf_path, state):
                logger.info("[%s] already up-to-date, skipping", key)
                continue
            process_pdf(key, pdf_path, config, state, logger, state_file)
        except Exception:
            logger.exception("worker error on %s", pdf_path)
        finally:
            work_queue.task_done()


def initial_sweep(work_queue: queue.Queue, storage: Path, state_file: Path, logger) -> None:
    state = load_state(state_file)
    pending = [(k, p) for k, p in scan_storage(storage) if needs_conversion(k, p, state)]
    logger.info("initial sweep: %d PDFs need conversion", len(pending))
    for k, p in pending:
        work_queue.put((k, p))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
    parser.add_argument("--no-initial-sweep", action="store_true", help="Skip scanning existing PDFs at startup.")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    log_dir = Path(config["log_dir"])
    logger = setup_logging(log_dir, "watcher")

    storage = Path(config["zotero_storage"])
    state_file = Path(config["state_file"])

    work_queue: queue.Queue = queue.Queue()

    worker = threading.Thread(
        target=worker_loop,
        args=(work_queue, config, logger, state_file),
        daemon=True,
        name="convert-worker",
    )
    worker.start()

    if not args.no_initial_sweep:
        initial_sweep(work_queue, storage, state_file, logger)

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
