"""Build an AI-readable index of the Zotero library, cross-referenced with
mineru-mirror MD files. Output: <output>/index.json

The index folds together:
  - Zotero collections (with parent/child hierarchy)
  - Zotero tags (as reverse index tag -> item keys)
  - Regular items (with title, authors, year, abstract, tags, collections)
  - Each item's attachments (with mineru MD status + path from state.json)
  - Each item's notes (Mineru-imported notes marked separately)

AI agents read index.json first to navigate the library the same way a human
would in Zotero (browse collection / filter by tag / look up paper). They
then follow `attachments[].md_path` to read the actual converted MD.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

LIB_ID = 12146168
API_BASE = "http://localhost:23119"


def get_json(path: str, params: dict | None = None) -> list | dict:
    if params:
        path = path + "?" + urllib.parse.urlencode(params)
    url = f"{API_BASE}{path}"
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.load(r)


def get_paginated(path: str, base_params: dict | None = None) -> list:
    """Walk Zotero API pagination via Link headers / start offset."""
    base_params = dict(base_params or {})
    base_params.setdefault("limit", 100)
    start = 0
    out: list = []
    while True:
        params = dict(base_params, start=start)
        batch = get_json(path, params)
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        if len(batch) < base_params["limit"]:
            break
        start += len(batch)
    return out


def strip_html(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def fetch_collections() -> dict:
    raw = get_paginated(f"/api/users/{LIB_ID}/collections")
    out: dict[str, dict] = {}
    for c in raw:
        d = c["data"]
        out[d["key"]] = {
            "key": d["key"],
            "name": d.get("name", ""),
            "parent": d.get("parentCollection") or None,
            "children": [],
        }
    # Wire children.
    for key, entry in out.items():
        p = entry["parent"]
        if p and p in out:
            out[p]["children"].append(key)
    # Build full path string for convenience.
    def path_of(k: str, seen: set | None = None) -> str:
        seen = seen or set()
        if k in seen or k not in out:
            return ""
        seen.add(k)
        e = out[k]
        if e["parent"]:
            return path_of(e["parent"], seen) + "/" + e["name"]
        return e["name"]
    for k, e in out.items():
        e["path"] = path_of(k)
    return out


def fetch_items() -> list:
    return get_paginated(
        f"/api/users/{LIB_ID}/items",
        base_params={"format": "json", "includeTrashed": 0},
    )


def fetch_children(parent_key: str) -> list:
    try:
        return get_paginated(
            f"/api/users/{LIB_ID}/items/{parent_key}/children",
            base_params={"format": "json"},
        )
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise


def load_mineru_state(state_file: Path) -> dict:
    if not state_file.exists():
        return {}
    with state_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_index(state_file: Path) -> dict:
    print("Fetching collections...", flush=True)
    collections = fetch_collections()
    print(f"  {len(collections)} collections")

    print("Fetching items...", flush=True)
    raw_items = fetch_items()
    print(f"  {len(raw_items)} total items (including attachments & notes)")

    mineru_state = load_mineru_state(state_file)

    # Bucket items by type and key.
    by_key = {it["data"]["key"]: it for it in raw_items}

    # We need parent items (regular bibliographic items) plus their children.
    regular_items: list = []
    for it in raw_items:
        d = it["data"]
        if d.get("deleted"):
            continue
        if d.get("itemType") in ("attachment", "note", "annotation"):
            continue
        regular_items.append(it)

    # Also include standalone PDFs (attachment with no parent) so they show up.
    standalone_attachments: list = []
    for it in raw_items:
        d = it["data"]
        if d.get("deleted"):
            continue
        if d.get("itemType") != "attachment":
            continue
        if d.get("parentItem"):
            continue
        if d.get("contentType") != "application/pdf":
            continue
        standalone_attachments.append(it)

    print(f"  {len(regular_items)} regular items + {len(standalone_attachments)} standalone PDFs")

    items_out: dict = {}
    tag_index: dict[str, list[str]] = {}

    def attachment_block(att_data: dict) -> dict:
        att_key = att_data["key"]
        mineru = mineru_state.get(att_key, {})
        return {
            "key": att_key,
            "title": att_data.get("title", ""),
            "filename": att_data.get("filename", ""),
            "content_type": att_data.get("contentType", ""),
            "linkMode": att_data.get("linkMode", ""),
            "mineru_status": mineru.get("status"),  # ok / failed / skipped_too_large / skipped_trashed / None
            "md_path": mineru.get("md_path"),
            "page_count": mineru.get("page_count"),
        }

    def note_block(note_data: dict) -> dict:
        body = note_data.get("note", "") or ""
        text = strip_html(body)
        title_match = re.match(r"<h1[^>]*>(.*?)</h1>", body, re.I | re.S)
        if title_match:
            title = strip_html(title_match.group(1))
        else:
            title = text[:80]
        return {
            "key": note_data["key"],
            "title": title,
            "is_mineru": title.startswith("Mineru MD:"),
            "char_count": len(text),
            "text_preview": text[:400],
        }

    def record_item(it: dict, fallback_creators: list | None = None):
        d = it["data"]
        key = d["key"]
        # Collect tags.
        tags = [t.get("tag") for t in d.get("tags", []) if t.get("tag")]
        for t in tags:
            tag_index.setdefault(t, []).append(key)

        # Children: attachments + notes.
        atts: list = []
        notes: list = []
        for child in fetch_children(key):
            cd = child["data"]
            if cd.get("deleted"):
                continue
            it = cd.get("itemType")
            if it == "attachment":
                atts.append(attachment_block(cd))
            elif it == "note":
                notes.append(note_block(cd))

        items_out[key] = {
            "key": key,
            "itemType": d.get("itemType"),
            "title": d.get("title", ""),
            "creators": d.get("creators", fallback_creators or []),
            "date": d.get("date", ""),
            "year": _extract_year(d.get("date", "")),
            "abstract": d.get("abstractNote", ""),
            "url": d.get("url", ""),
            "DOI": d.get("DOI", ""),
            "publicationTitle": d.get("publicationTitle", ""),
            "tags": tags,
            "collections": d.get("collections", []),
            "attachments": atts,
            "notes": notes,
        }

    for i, it in enumerate(regular_items, 1):
        record_item(it)
        if i % 20 == 0:
            print(f"  indexed {i}/{len(regular_items)} regular items", flush=True)

    # Standalone PDFs: synthesize a pseudo-item so AI sees them too.
    for it in standalone_attachments:
        d = it["data"]
        key = d["key"]
        tags = [t.get("tag") for t in d.get("tags", []) if t.get("tag")]
        for t in tags:
            tag_index.setdefault(t, []).append(key)
        items_out[key] = {
            "key": key,
            "itemType": "standalone-pdf",
            "title": d.get("title", "").rsplit(".pdf", 1)[0],
            "creators": [],
            "date": "",
            "year": None,
            "abstract": "",
            "url": "",
            "DOI": "",
            "publicationTitle": "",
            "tags": tags,
            "collections": d.get("collections", []),
            "attachments": [attachment_block(d)],
            "notes": [],
        }

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "library_id": LIB_ID,
        "summary": {
            "total_items_in_index": len(items_out),
            "total_collections": len(collections),
            "total_tags": len(tag_index),
            "items_with_md": sum(
                1 for v in items_out.values()
                if any(a.get("mineru_status") == "ok" for a in v["attachments"])
            ),
        },
        "collections": collections,
        "tags": {k: sorted(set(v)) for k, v in tag_index.items()},
        "items": items_out,
    }


_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
def _extract_year(date_str: str) -> int | None:
    if not date_str:
        return None
    m = _YEAR_RE.search(date_str)
    return int(m.group()) if m else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--state",
        default=r"C:\Users\Administrator\zotero-mineru\state.json",
        help="Path to mineru state.json",
    )
    parser.add_argument(
        "--out",
        default=r"C:\Users\Administrator\Zotero\mineru-mirror\index.json",
        help="Output index path",
    )
    args = parser.parse_args()

    t0 = time.time()
    idx = build_index(Path(args.state))
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    print()
    print(f"wrote {out_path}  ({out_path.stat().st_size:,} bytes)  in {time.time()-t0:.1f}s")
    print(f"summary: {idx['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
