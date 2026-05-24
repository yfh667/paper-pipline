"""Walk Zotero/storage, hit local API for each attachment, report orphan stats."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

STORAGE = Path(r"C:\Users\Administrator\Zotero\storage")
LIB_ID = 12146168

orphans: list[tuple[str, str]] = []
parented: list[tuple[str, str]] = []
errors: list[tuple[str, str]] = []

keys = [d.name for d in STORAGE.iterdir() if d.is_dir() and any(d.glob("*.pdf"))]
print(f"checking {len(keys)} attachments...", flush=True)

for i, key in enumerate(keys, 1):
    url = f"http://localhost:23119/api/users/{LIB_ID}/items/{key}?format=json"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            d = json.load(r)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        errors.append((key, str(e)))
        continue
    title = d["data"].get("title", "")
    parent = d["data"].get("parentItem")
    if parent:
        parented.append((key, title))
    else:
        orphans.append((key, title))
    if i % 20 == 0:
        print(f"  {i}/{len(keys)}", flush=True)

print(f"\n=== summary ===")
print(f"orphans (no parent item): {len(orphans)}")
print(f"parented (proper item)  : {len(parented)}")
print(f"errors                  : {len(errors)}")

if orphans:
    print(f"\n=== orphan list ({len(orphans)}) ===")
    for k, t in orphans:
        print(f"  {k}  {t}")

if errors:
    print(f"\n=== errors ===")
    for k, e in errors:
        print(f"  {k}  {e}")
