"""Find converted PDFs that are both alive in Zotero AND have a parent item."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

with open(r"C:\Users\Administrator\zotero-mineru\state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

ok_keys = [k for k, v in state.items() if v.get("status") == "ok"]
print(f"{len(ok_keys)} keys have converted MD; checking which are alive + have parent...")

testable: list[tuple[str, str, str]] = []
for k in ok_keys:
    try:
        with urllib.request.urlopen(
            f"http://localhost:23119/api/users/12146168/items/{k}?format=json", timeout=5
        ) as r:
            d = json.load(r)
    except Exception:
        continue
    data = d["data"]
    if data.get("deleted"):
        continue
    parent = data.get("parentItem")
    if not parent:
        continue
    title = data.get("title", "")
    testable.append((k, parent, title))

print(f"\nReady-to-test items ({len(testable)}):")
for k, parent, title in testable:
    print(f"  PDF [{k}]  parent [{parent}]")
    print(f"    {title[:90]}")
    print(f"    jump URL: zotero://select/library/items/{parent}")
