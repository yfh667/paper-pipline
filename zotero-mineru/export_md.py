"""Export MD files matching filter conditions into a single output folder.

Takes the same filters as zotero_query.py (tag / collection / search / year /
author / --has-md) but instead of printing JSON, COPIES the matching MD files
into --out, with companion metadata JSONs and a manifest. Use this when you
want to feed a curated subset of papers to Obsidian / another AI agent /
plain reading.

Examples:
  # Flat output (default): all MDs in one folder, no images
  python export_md.py --collection "100papers" --out C:\export\100papers

  # Per-paper folders with images (Obsidian-style vault)
  python export_md.py --tag 路由 --year-min 2020 \\
      --out C:\export\routing-2020 --layout perdoc --with-images

  # Just dump everything that has an MD into one place
  python export_md.py --has-md --out C:\export\all-md
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Reuse the filtering logic from zotero_query so behavior matches exactly.
sys.path.insert(0, str(Path(__file__).parent))
from zotero_query import filter_items, load_index, slim_item  # noqa: E402

DEFAULT_INDEX = Path(r"C:\Users\Administrator\Zotero\mineru-mirror\index.json")

_INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_TRAILING_DOTS_SPACES = re.compile(r"[\.\s]+$")


def sanitize_filename(name: str, max_len: int = 120) -> str:
    """Make a filesystem-safe filename, preserving readable Chinese / English."""
    s = _INVALID.sub("_", name)
    s = _TRAILING_DOTS_SPACES.sub("", s).strip()
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return s or "untitled"


def build_basename(item: dict, attachment: dict) -> str:
    """Pick a recognizable filename: prefer item title, fall back to attachment."""
    title = (item.get("title") or "").strip()
    year = item.get("year")
    if title:
        if year:
            return sanitize_filename(f"{year} - {title}")
        return sanitize_filename(title)
    # Standalone or untitled: use the original PDF basename, minus extension.
    att_title = attachment.get("title") or attachment.get("filename") or attachment.get("key") or "untitled"
    return sanitize_filename(att_title.rsplit(".pdf", 1)[0])


def export_meta(item: dict, idx: dict, source_md: Path) -> dict:
    """Build a per-paper metadata sidecar."""
    coll_paths = []
    for ck in item.get("collections") or []:
        c = idx["collections"].get(ck)
        if c:
            coll_paths.append(c.get("path") or c.get("name"))
    return {
        "key": item["key"],
        "title": item.get("title"),
        "year": item.get("year"),
        "date": item.get("date"),
        "creators": [
            {
                "lastName": c.get("lastName") or "",
                "firstName": c.get("firstName") or "",
                "type": c.get("creatorType") or "",
            }
            for c in (item.get("creators") or [])
        ],
        "publicationTitle": item.get("publicationTitle"),
        "DOI": item.get("DOI"),
        "url": item.get("url"),
        "abstract": item.get("abstract"),
        "tags": item.get("tags") or [],
        "collections": coll_paths,
        "source_md_path": str(source_md),
        "source_mirror_key": source_md.parent.parent.name if source_md.parent.name == "hybrid_auto" else source_md.parent.name,
    }


def copy_flat(item: dict, attachment: dict, src_md: Path, out_dir: Path, idx: dict) -> dict:
    basename = build_basename(item, attachment)
    target_md = out_dir / f"{basename}.md"
    target_meta = out_dir / f"{basename}.meta.json"

    # Disambiguate if collision (different keys / different versions).
    if target_md.exists():
        target_md = out_dir / f"{basename} [{item['key']}].md"
        target_meta = out_dir / f"{basename} [{item['key']}].meta.json"

    shutil.copy2(src_md, target_md)
    with target_meta.open("w", encoding="utf-8") as f:
        json.dump(export_meta(item, idx, src_md), f, ensure_ascii=False, indent=2)

    return {
        "key": item["key"],
        "title": item.get("title"),
        "year": item.get("year"),
        "exported_md": str(target_md),
        "exported_meta": str(target_meta),
    }


def copy_perdoc(item: dict, attachment: dict, src_md: Path, out_dir: Path, idx: dict, with_images: bool) -> dict:
    basename = build_basename(item, attachment)
    folder = out_dir / basename
    if folder.exists():
        folder = out_dir / f"{basename} [{item['key']}]"
    folder.mkdir(parents=True, exist_ok=True)

    target_md = folder / f"{basename}.md"
    shutil.copy2(src_md, target_md)

    # Companion metadata
    with (folder / "meta.json").open("w", encoding="utf-8") as f:
        json.dump(export_meta(item, idx, src_md), f, ensure_ascii=False, indent=2)

    # Images folder (mineru emits relative ./images/<hash>.jpg in MD)
    if with_images:
        src_images = src_md.parent / "images"
        if src_images.is_dir():
            shutil.copytree(src_images, folder / "images", dirs_exist_ok=True)

    return {
        "key": item["key"],
        "title": item.get("title"),
        "year": item.get("year"),
        "exported_dir": str(folder),
        "exported_md": str(target_md),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Copy filtered MDs into an output folder.",
        epilog=__doc__,
    )
    parser.add_argument("--index", default=str(DEFAULT_INDEX))
    parser.add_argument("--out", required=True, help="Output folder (will be created)")
    parser.add_argument(
        "--layout",
        choices=["flat", "perdoc"],
        default="flat",
        help="flat: one MD per item at top level. perdoc: subfolder per paper (good for Obsidian).",
    )
    parser.add_argument("--with-images", action="store_true",
                        help="(only meaningful with --layout perdoc) also copy images/ folder for each paper")
    parser.add_argument("--clear", action="store_true",
                        help="Wipe --out before exporting (use with care)")
    parser.add_argument("--dry-run", action="store_true")

    # Same filter args as zotero_query.py "items"
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--collection", action="append", default=[])
    parser.add_argument("--search")
    parser.add_argument("--year-min", type=int)
    parser.add_argument("--year-max", type=int)
    parser.add_argument("--author")
    parser.add_argument("--has-md", action="store_true",
                        help="Only items that have an OK mineru MD (recommended; otherwise no-op)")
    parser.add_argument("--limit", type=int, default=0)

    args = parser.parse_args()

    idx = load_index(Path(args.index))
    # Force has_md True for export — items without MD are unexportable anyway.
    args.has_md = True
    matched = filter_items(idx, args)
    if args.limit:
        matched = matched[: args.limit]

    print(f"Filter matched {len(matched)} item(s) with an MD.")
    if args.dry_run:
        for it in matched:
            md_paths = [a["md_path"] for a in (it.get("attachments") or []) if a.get("mineru_status") == "ok"]
            print(f"  [{it['key']}] {it.get('title','(no title)')[:80]}  ({len(md_paths)} md)")
        return 0

    out_dir = Path(args.out)
    if args.clear and out_dir.exists():
        print(f"clearing existing {out_dir}")
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    for it in matched:
        for att in it.get("attachments") or []:
            if att.get("mineru_status") != "ok":
                continue
            md_path = att.get("md_path")
            if not md_path:
                continue
            src_md = Path(md_path)
            if not src_md.exists():
                print(f"  [{it['key']}] WARN: md_path missing on disk: {src_md}")
                continue
            try:
                if args.layout == "flat":
                    rec = copy_flat(it, att, src_md, out_dir, idx)
                else:
                    rec = copy_perdoc(it, att, src_md, out_dir, idx, args.with_images)
                manifest.append(rec)
                print(f"  [{it['key']}] -> {rec.get('exported_md')}")
            except Exception as e:
                print(f"  [{it['key']}] ERROR: {e}")

    manifest_path = out_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "exported_at": datetime.now().isoformat(timespec="seconds"),
                "filter": {
                    "tag": args.tag,
                    "collection": args.collection,
                    "search": args.search,
                    "year_min": args.year_min,
                    "year_max": args.year_max,
                    "author": args.author,
                    "limit": args.limit,
                },
                "layout": args.layout,
                "with_images": args.with_images,
                "count": len(manifest),
                "items": manifest,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print(f"Exported {len(manifest)} MD(s) to {out_dir}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
