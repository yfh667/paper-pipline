"""Scan all PDFs in Zotero storage and convert any that haven't been converted yet.

By default, PDFs above config['max_pages'] are skipped as too-large. Use
--large yes to process them via split-mode (each chunk is converted
separately, then MDs and images are merged). --large ask (default) prompts
interactively when previously-skipped large PDFs exist or when the run
would encounter new ones.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import (
    get_pdf_page_count,
    load_config,
    load_state,
    needs_conversion,
    process_pdf,
    save_state,
    scan_storage,
    setup_logging,
)


def find_large_skipped(state: dict, max_pages: int) -> list[str]:
    return [
        k for k, v in state.items()
        if v.get("status") == "skipped_too_large"
        and (v.get("page_count") or 0) > max_pages
    ]


def reset_status(state: dict, keys: list[str]) -> None:
    """Drop status field on the given keys so needs_conversion returns True."""
    for k in keys:
        if k in state:
            state[k].pop("status", None)
            state[k]["last_error"] = "re-processing as large (split mode)"


def prompt_yes_no(question: str, default_no: bool = True) -> bool:
    if not sys.stdin or not sys.stdin.isatty():
        # Non-interactive — fall back to default.
        return not default_no
    suffix = " [y/N]: " if default_no else " [Y/n]: "
    try:
        ans = input(question + suffix).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    if not ans:
        return not default_no
    return ans in ("y", "yes")


def decide_large(args, state: dict, config: dict, logger) -> bool:
    """Returns True if the run should process large PDFs (via split-mode)."""
    max_pages = int(config.get("max_pages", 0))
    if args.large == "yes":
        return True
    if args.large == "no":
        return False
    # args.large == "ask"
    skipped_large = find_large_skipped(state, max_pages)
    if skipped_large:
        msg = (f"\n{len(skipped_large)} PDF(s) were previously skipped as too-large "
               f"(>{max_pages} pages).\nProcess them now in split-mode (each split into "
               f"{config.get('split_chunk_pages', 200)}-page chunks, slower)?")
        return prompt_yes_no(msg, default_no=True)
    # No previously-skipped; ask anyway about new large ones we might encounter.
    msg = (f"\nDo you want to process PDFs larger than {max_pages} pages "
           f"using split-mode? (slower, ~per-chunk runtime)")
    return prompt_yes_no(msg, default_no=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
    parser.add_argument("--dry-run", action="store_true", help="Only list what would be converted.")
    parser.add_argument("--limit", type=int, default=0, help="Stop after N conversions (0 = no limit).")
    parser.add_argument("--key", default=None, help="Only process this Zotero key.")
    parser.add_argument("--force", action="store_true", help="Re-convert even if state says ok.")
    parser.add_argument(
        "--large",
        choices=["ask", "yes", "no"],
        default="ask",
        help="Whether to process PDFs above max_pages by splitting + merging. "
             "ask (default) prompts interactively; yes/no skip the prompt.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    log_dir = Path(config["log_dir"])
    logger = setup_logging(log_dir, "batch")

    storage = Path(config["zotero_storage"])
    state_file = Path(config["state_file"])
    state = load_state(state_file)

    if args.force:
        # Clear status so needs_conversion returns True.
        for k in list(state.keys()):
            state[k].pop("status", None)
        save_state(state_file, state)

    # Decide whether to process large PDFs (interactive if --large=ask).
    process_large = decide_large(args, state, config, logger)
    config["process_large"] = process_large
    if process_large:
        max_pages = int(config.get("max_pages", 0))
        unskip = find_large_skipped(state, max_pages)
        if unskip:
            reset_status(state, unskip)
            save_state(state_file, state)
            logger.info("re-queued %d previously skipped large PDF(s) for split-mode: %s",
                        len(unskip), unskip[:5])
        logger.info("LARGE-PDF processing: ENABLED (split-mode, chunk=%d pages)",
                    int(config.get("split_chunk_pages", 200)))
    else:
        logger.info("LARGE-PDF processing: DISABLED (PDFs > %d pages will be marked skipped_too_large)",
                    int(config.get("max_pages", 0)))

    pdfs = scan_storage(storage)
    if args.key:
        pdfs = [(k, p) for k, p in pdfs if k == args.key]

    pending = [(k, p) for k, p in pdfs if needs_conversion(k, p, state)]
    logger.info("scanned %d PDFs, %d need conversion", len(pdfs), len(pending))

    if args.dry_run:
        for k, p in pending:
            try:
                pc = get_pdf_page_count(p)
            except Exception:
                pc = None
            tag = ""
            if pc is not None and pc > int(config.get("max_pages", 0)):
                tag = f"  [LARGE {pc} pages -> {'split' if process_large else 'will skip'}]"
            logger.info("[dry-run] %s -> %s%s", k, p.name, tag)
        return 0

    converted = 0
    errored = 0
    for k, p in pending:
        if args.limit and converted >= args.limit:
            logger.info("hit --limit %d, stopping", args.limit)
            break
        try:
            if process_pdf(k, p, config, state, logger, state_file):
                converted += 1
        except Exception:
            errored += 1
            logger.exception("[%s] unhandled error; continuing with next PDF", k)

    logger.info("done: %d converted, %d errored", converted, errored)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
