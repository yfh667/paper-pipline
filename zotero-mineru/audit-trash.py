"""Audit: which of our scanned PDF attachment keys are in Zotero's trash?"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

LIB_ID = 12146168
STORAGE = Path(r"C:\Users\Administrator\Zotero\storage")

keys = [d.name for d in STORAGE.iterdir() if d.is_dir() and any(d.glob("*.pdf"))]

alive: list[tuple[str, str]] = []
trashed: list[tuple[str, str]] = []
missing: list[tuple[str, str]] = []
errors: list[tuple[str, str]] = []

print(f"checking {len(keys)} attachment keys against Zotero API...", flush=True)
for i, key in enumerate(keys, 1):
    url = f"http://localhost:23119/api/users/{LIB_ID}/items/{key}?format=json"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            missing.append((key, "not in Zotero DB"))
        else:
            errors.append((key, f"HTTP {e.code}"))
        continue
    except Exception as e:
        errors.append((key, str(e)))
        continue
    data = d.get("data", {})
    title = data.get("title", "")
    if data.get("deleted"):
        trashed.append((key, title))
    else:
        alive.append((key, title))
    if i % 20 == 0:
        print(f"  {i}/{len(keys)}", flush=True)

print()
print(f"=== summary of {len(keys)} attachments ===")
print(f"  alive (in library): {len(alive)}")
print(f"  trashed           : {len(trashed)}")
print(f"  missing in DB     : {len(missing)}")
print(f"  errors            : {len(errors)}")

if trashed:
    print(f"\n=== trashed ({len(trashed)}) ===")
    for k, t in trashed:
        print(f"  [{k}] {t[:90]}")

if missing:
    print(f"\n=== missing in DB ({len(missing)}) ===")
    for k, t in missing:
        print(f"  [{k}] {t}")

if errors:
    print(f"\n=== errors ===")
    for k, e in errors:
        print(f"  [{k}] {e}")
