"""Query the Zotero index built by build_index.py.

Designed for both human and AI agent use. Outputs JSON to stdout so AI agents
can parse it directly via tool-use; human readers get a pretty-printed summary
via --pretty.

Usage examples:
  python zotero_query.py collections                       # list collection tree
  python zotero_query.py tags                              # all tags + counts
  python zotero_query.py tags --min-count 2                # only tags used >= 2 times
  python zotero_query.py items --tag 100papers             # items tagged 100papers
  python zotero_query.py items --collection "SatNet"       # items in collection (name match)
  python zotero_query.py items --search "Hypatia"          # search title+abstract
  python zotero_query.py items --year-min 2020             # filter by year
  python zotero_query.py items --has-md                    # only items with converted MD
  python zotero_query.py show <ITEM_KEY>                   # full record for one item
  python zotero_query.py md-paths --tag 100papers          # just the MD file paths
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_INDEX = Path(r"C:\Users\Administrator\Zotero\mineru-mirror\index.json")


def load_index(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def emit(obj, pretty: bool = False) -> None:
    if pretty:
        json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        json.dump(obj, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")


# ---- filters ---------------------------------------------------------------

def filter_items(idx: dict, args) -> list[dict]:
    items = list(idx["items"].values())

    if args.tag:
        # match any of the listed tags (OR)
        wanted = set(args.tag)
        items = [it for it in items if wanted.intersection(it.get("tags") or [])]

    if args.collection:
        coll = idx["collections"]
        matches: set[str] = set()
        for k, c in coll.items():
            for needle in args.collection:
                if needle.lower() in (c.get("name") or "").lower() or needle.lower() in (c.get("path") or "").lower():
                    matches.add(k)
        if matches:
            items = [it for it in items if matches.intersection(it.get("collections") or [])]
        else:
            items = []

    if args.search:
        q = args.search.lower()
        def haystack(it):
            parts = [
                it.get("title", ""),
                it.get("abstract", ""),
                " ".join(
                    f"{c.get('lastName','')} {c.get('firstName','')}"
                    for c in (it.get("creators") or [])
                ),
            ]
            return " ".join(parts).lower()
        items = [it for it in items if q in haystack(it)]

    if args.year_min is not None:
        items = [it for it in items if (it.get("year") or 0) >= args.year_min]
    if args.year_max is not None:
        items = [it for it in items if (it.get("year") or 9999) <= args.year_max]

    if args.has_md:
        items = [
            it for it in items
            if any(a.get("mineru_status") == "ok" for a in it.get("attachments") or [])
        ]
    if args.author:
        a = args.author.lower()
        items = [
            it for it in items
            if any(
                a in (c.get("lastName") or "").lower() or a in (c.get("firstName") or "").lower()
                for c in (it.get("creators") or [])
            )
        ]

    return items


def slim_item(it: dict, idx: dict) -> dict:
    """Compact representation suitable for AI consumption."""
    coll_names = []
    for ck in it.get("collections") or []:
        c = idx["collections"].get(ck)
        if c:
            coll_names.append(c.get("path") or c.get("name"))
    md_paths = [a.get("md_path") for a in (it.get("attachments") or []) if a.get("md_path")]
    return {
        "key": it["key"],
        "title": it.get("title"),
        "year": it.get("year"),
        "creators": [
            (c.get("lastName") or "") + (", " + c.get("firstName") if c.get("firstName") else "")
            for c in (it.get("creators") or [])
        ],
        "tags": it.get("tags") or [],
        "collections": coll_names,
        "md_paths": md_paths,
        "has_md": bool(md_paths),
        "note_count": len(it.get("notes") or []),
        "abstract_excerpt": (it.get("abstract") or "")[:200],
    }


# ---- subcommands -----------------------------------------------------------

def cmd_collections(idx: dict, args) -> int:
    out = []
    for k, c in idx["collections"].items():
        out.append({"key": k, "name": c["name"], "path": c["path"],
                    "parent": c.get("parent"), "child_count": len(c.get("children") or [])})
    out.sort(key=lambda x: x["path"])
    emit(out, pretty=args.pretty)
    return 0


def cmd_tags(idx: dict, args) -> int:
    rows = [{"tag": t, "count": len(keys)} for t, keys in idx["tags"].items()]
    rows = [r for r in rows if r["count"] >= (args.min_count or 0)]
    rows.sort(key=lambda r: (-r["count"], r["tag"]))
    emit(rows, pretty=args.pretty)
    return 0


def cmd_items(idx: dict, args) -> int:
    matches = filter_items(idx, args)
    matches.sort(key=lambda x: (-(x.get("year") or 0), (x.get("title") or "")))
    if args.limit:
        matches = matches[: args.limit]
    out = [slim_item(it, idx) for it in matches]
    emit({"count": len(out), "items": out}, pretty=args.pretty)
    return 0


def cmd_show(idx: dict, args) -> int:
    it = idx["items"].get(args.key)
    if not it:
        emit({"error": f"key {args.key} not found"}, pretty=args.pretty)
        return 1
    # Resolve collection names for readability.
    coll_paths = []
    for ck in it.get("collections") or []:
        c = idx["collections"].get(ck)
        if c:
            coll_paths.append(c["path"])
    out = dict(it)
    out["collection_paths"] = coll_paths
    emit(out, pretty=args.pretty)
    return 0


def cmd_md_paths(idx: dict, args) -> int:
    matches = filter_items(idx, args)
    paths: list[str] = []
    for it in matches:
        for a in it.get("attachments") or []:
            if a.get("mineru_status") == "ok" and a.get("md_path"):
                paths.append(a["md_path"])
    emit(paths, pretty=args.pretty)
    return 0


# ---- arg plumbing ----------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--index", default=str(DEFAULT_INDEX))
    p.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("collections")

    pt = sub.add_parser("tags")
    pt.add_argument("--min-count", type=int, default=0)

    def add_filters(sp):
        sp.add_argument("--tag", action="append", default=[], help="filter by tag (can repeat for OR)")
        sp.add_argument("--collection", action="append", default=[], help="filter by collection name/path (substring)")
        sp.add_argument("--search", help="substring search in title/abstract/authors")
        sp.add_argument("--year-min", type=int)
        sp.add_argument("--year-max", type=int)
        sp.add_argument("--author", help="substring match in any creator's name")
        sp.add_argument("--has-md", action="store_true", help="only items whose attachment has an OK mineru MD")
        sp.add_argument("--limit", type=int, default=0)

    pi = sub.add_parser("items")
    add_filters(pi)

    pm = sub.add_parser("md-paths")
    add_filters(pm)

    ps = sub.add_parser("show")
    ps.add_argument("key")

    return p


def main() -> int:
    args = build_parser().parse_args()
    idx = load_index(Path(args.index))
    return {
        "collections": cmd_collections,
        "tags": cmd_tags,
        "items": cmd_items,
        "show": cmd_show,
        "md-paths": cmd_md_paths,
    }[args.command](idx, args)


if __name__ == "__main__":
    raise SystemExit(main())
