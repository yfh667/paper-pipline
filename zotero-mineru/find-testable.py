"""Find converted PDFs that are both alive in Zotero AND have a parent item."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

config_path = Path(__file__).with_name("config.json")
config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
state_path = Path(config.get("state_file", str(Path(__file__).with_name("state.json"))))
api_base = config.get("zotero_api_base", "http://localhost:23119").rstrip("/")
library_id = config.get("zotero_library_id", 12146168)

with state_path.open("r", encoding="utf-8") as f:
    state = json.load(f)

ok_keys = [k for k, v in state.items() if v.get("status") == "ok"]
print(f"{len(ok_keys)} keys have converted MD; checking which are alive + have parent...")

testable: list[tuple[str, str, str]] = []
for k in ok_keys:
    try:
        with urllib.request.urlopen(
            f"{api_base}/api/users/{library_id}/items/{k}?format=json", timeout=5
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
