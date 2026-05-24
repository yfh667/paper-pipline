"""One-shot dashboard: tell the user what every part of the pipeline has done.

Run anytime to see:
  - Where each file lives and when it was last touched
  - Mineru batch progress (converted / failed / skipped breakdown)
  - Index freshness (when built, what it covers, gaps)
  - Recent log activity
  - Action items (things that need human attention)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(r"C:\Users\Administrator\zotero-mineru")
MIRROR = Path(r"C:\Users\Administrator\Zotero\mineru-mirror")
STORAGE = Path(r"C:\Users\Administrator\Zotero\storage")

STATE_FILE = ROOT / "state.json"
INDEX_FILE = MIRROR / "index.json"
LOG_DIR = ROOT / "logs"
CONFIG_FILE = ROOT / "config.json"


def fmt_age(ts: datetime) -> str:
    delta = datetime.now() - ts
    if delta < timedelta(minutes=1):
        return "just now"
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() / 60)} min ago"
    if delta < timedelta(days=1):
        return f"{int(delta.total_seconds() / 3600)} h ago"
    return f"{delta.days} d ago"


def file_age(path: Path) -> str:
    if not path.exists():
        return "missing"
    return fmt_age(datetime.fromtimestamp(path.stat().st_mtime))


def banner(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


# ---------- 1. Files inventory --------------------------------------------

def files_section() -> None:
    banner("FILES")
    rows = [
        ("config.json", CONFIG_FILE, "pipeline configuration"),
        ("state.json", STATE_FILE, "per-PDF conversion state"),
        ("index.json", INDEX_FILE, "AI-readable Zotero index"),
        ("watcher log (today)", LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log",
         "today's batch/watcher activity"),
        ("mineru-mirror/", MIRROR, "all converted MDs"),
    ]
    for label, path, desc in rows:
        if path.exists():
            if path.is_file():
                size = f"{path.stat().st_size:,} B"
            else:
                size = f"{sum(1 for _ in path.rglob('*'))} entries"
            print(f"  {label:25s} {size:>15s}  {file_age(path):>12s}   {desc}")
        else:
            print(f"  {label:25s} {'(missing)':>15s} {'':>12s}   {desc}")


# ---------- 2. Mineru batch progress --------------------------------------

def batch_section() -> dict:
    banner("MINERU BATCH")
    if not STATE_FILE.exists():
        print("  state.json not found — batch has never run.")
        return {}

    with STATE_FILE.open("r", encoding="utf-8") as f:
        state = json.load(f)

    # Scan storage for total PDF count.
    total_pdfs = sum(1 for d in STORAGE.iterdir() if d.is_dir() and any(d.glob("*.pdf")))
    status_counts = Counter(v.get("status", "?") for v in state.values())
    tracked = len(state)
    untouched = total_pdfs - tracked

    print(f"  total PDFs in Zotero storage : {total_pdfs}")
    print(f"  tracked in state.json        : {tracked}")
    print(f"  not yet processed            : {untouched}")
    print()
    for status in ("ok", "skipped_trashed", "skipped_too_large", "failed"):
        n = status_counts.get(status, 0)
        if n:
            print(f"    {status:25s} {n}")

    return state


# ---------- 3. Index freshness --------------------------------------------

def index_section(state: dict) -> None:
    banner("INDEX (AI's view of Zotero)")
    if not INDEX_FILE.exists():
        print("  index.json not built yet. Run:")
        print(r"    python C:\Users\Administrator\zotero-mineru\build_index.py")
        return

    with INDEX_FILE.open("r", encoding="utf-8") as f:
        idx = json.load(f)
    generated = idx.get("generated_at", "")
    summary = idx.get("summary", {})
    try:
        gen_dt = datetime.fromisoformat(generated)
        age = fmt_age(gen_dt)
    except ValueError:
        age = "?"

    print(f"  generated_at         : {generated}  ({age})")
    print(f"  items in index       : {summary.get('total_items_in_index')}")
    print(f"  collections          : {summary.get('total_collections')}")
    print(f"  tags                 : {summary.get('total_tags')}")
    print(f"  items_with_md        : {summary.get('items_with_md')}")
    print()

    # Drift check: are there ok mineru entries the index hasn't picked up?
    state_ok = {k for k, v in state.items() if v.get("status") == "ok"}
    indexed_attachments = set()
    for it in idx.get("items", {}).values():
        for a in it.get("attachments") or []:
            if a.get("md_path"):
                indexed_attachments.add(a["key"])
    new_since_index = state_ok - indexed_attachments
    if new_since_index:
        print(f"  [!] {len(new_since_index)} MD(s) converted since last index build:")
        for k in list(new_since_index)[:5]:
            print(f"      [{k}]")
        if len(new_since_index) > 5:
            print(f"      ... and {len(new_since_index) - 5} more")
        print(f"    -> rebuild index to expose them to AI:")
        print(r"      python C:\Users\Administrator\zotero-mineru\build_index.py")
    else:
        print("  [OK] index is in sync with mineru state")


# ---------- 4. Recent log tail --------------------------------------------

def logs_section() -> None:
    banner("RECENT LOG (last 12 lines)")
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not logs:
        print("  no logs found")
        return
    latest = logs[0]
    print(f"  from {latest.name}  (modified {file_age(latest)})")
    with latest.open("r", encoding="utf-8") as f:
        lines = f.readlines()[-12:]
    for line in lines:
        print("  " + line.rstrip())


# ---------- 5. Action items -----------------------------------------------

def actions_section(state: dict) -> None:
    banner("ACTION ITEMS (what you can do next)")
    items: list[str] = []

    # Pending conversions
    if state:
        ok = sum(1 for v in state.values() if v.get("status") == "ok")
        total_in_storage = sum(1 for d in STORAGE.iterdir() if d.is_dir() and any(d.glob("*.pdf")))
        pending = total_in_storage - len(state)
        if pending > 0:
            items.append(
                f"{pending} PDF(s) haven't been processed yet. "
                f"Run: run-batch.ps1  (or wait for watcher if running)"
            )
        failed = [k for k, v in state.items() if v.get("status") == "failed"]
        if failed:
            items.append(f"{len(failed)} failed conversion(s): {failed[:3]} (see logs for reason)")

    # Index freshness
    if INDEX_FILE.exists() and STATE_FILE.exists():
        with INDEX_FILE.open("r", encoding="utf-8") as f:
            idx = json.load(f)
        try:
            gen_dt = datetime.fromisoformat(idx.get("generated_at", ""))
            if datetime.now() - gen_dt > timedelta(hours=24):
                items.append("Index is >24 h old. Run build_index.py if you've added tags / collections / items.")
        except ValueError:
            pass

    if not INDEX_FILE.exists():
        items.append("Index never built. Run: python build_index.py")

    # Items with MD but no parent (AI sees them but with no metadata)
    if STATE_FILE.exists() and INDEX_FILE.exists():
        with INDEX_FILE.open("r", encoding="utf-8") as f:
            idx = json.load(f)
        standalone_with_md = 0
        for it in idx.get("items", {}).values():
            if it.get("itemType") == "standalone-pdf":
                if any(a.get("mineru_status") == "ok" for a in it.get("attachments") or []):
                    standalone_with_md += 1
        if standalone_with_md:
            items.append(
                f"{standalone_with_md} converted PDF(s) are standalone (no parent item with metadata). "
                "AI will see them but with no title/author/year. Right-click in Zotero -> Create Parent Item / Retrieve Metadata."
            )

    if not items:
        print("  (nothing pending — pipeline is happy)")
    else:
        for i, msg in enumerate(items, 1):
            print(f"  {i}. {msg}")


def main() -> int:
    files_section()
    state = batch_section()
    index_section(state)
    logs_section()
    actions_section(state)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
