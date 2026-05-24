"""Quick progress dump from state.json."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

state_path = Path(r"C:\Users\Administrator\zotero-mineru\state.json")
with state_path.open("r", encoding="utf-8") as f:
    state = json.load(f)

status_counts: Counter[str] = Counter()
for v in state.values():
    status_counts[v.get("status", "unknown")] += 1

print(f"state entries: {len(state)}")
for s, n in status_counts.most_common():
    print(f"  {s:25s} {n}")

print()
print("--- ok ---")
for k, v in state.items():
    if v.get("status") != "ok":
        continue
    pdf = v.get("pdf_path", "")
    name = Path(pdf).name if pdf else ""
    pc = v.get("page_count", "?")
    print(f"[{k}] {pc:>4} pages  {name[:90]}")
    print(f"        md: {v.get('md_path')}")
