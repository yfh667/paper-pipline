"""Apply an AI/human "decisions.json" to paperlist_clean.txt + paperlist_review.json.

decisions.json schema:

    {
      "accepts": [
        {"tag": "ieee",
         "title": "Final title to write into clean.txt",
         "doi": "10.1109/...",
         "match": "CMAP"}                  # substring of the review entry's title/url
      ],
      "manual": [
        {"match": "Starlink Constellation: Deployment",
         "reason": "no good CrossRef match — user must find DOI by hand"}
      ],
      "noise": [
        {"match": "wikipedia.org/wiki/Guowang"}      # discard entirely
      ]
    }

Effects:
  - Every accept   -> appended to paperlist_clean.txt as `[tag] title  (doi=doi)`
                      and the review entry with matching title/url is removed
  - Every manual   -> entry stays in paperlist_review.json but moves to top with
                      a "manual" reason marker (so user sees them clearly)
  - Every noise    -> entry removed entirely from paperlist_review.json

After running, paperlist_review.json contains only entries that:
  - You haven't yet processed (no decision)
  - Were flagged as "manual" — handed over to the user

Re-running with --sort sorts clean.txt by tag+title.

Usage:
    python apply_decisions.py decisions.json
    python apply_decisions.py decisions.json --clean output/paperlist_clean.txt \
                                              --review output/paperlist_review.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CLEAN = PROJECT_ROOT / "output" / "paperlist_clean.txt"
DEFAULT_REVIEW = PROJECT_ROOT / "output" / "paperlist_review.json"

CLEAN_LINE_RE = re.compile(r"^\[([\w\-]+)\]\s+(.+?)\s+\(doi=([^)]*)\)\s*$")


def load_clean(path: Path) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        m = CLEAN_LINE_RE.match(line)
        if m:
            rows.append((m.group(1), m.group(2), m.group(3)))
    return rows


def write_clean(path: Path, rows: list[tuple[str, str, str]]) -> None:
    rows = sorted(set(rows), key=lambda r: (r[0], r[1].lower()))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(f"[{t}] {title}  (doi={doi})" for t, title, doi in rows) + "\n",
        encoding="utf-8",
    )


def entry_text(e: dict) -> str:
    """Concatenated searchable text for an entry (title + url + candidates titles)."""
    parts = [e.get("title", ""), e.get("url", "")]
    for c in e.get("candidates") or []:
        parts.append(c.get("title", ""))
        parts.append(c.get("doi", ""))
    return " | ".join(parts).lower()


def match_entry(entry: dict, needle: str) -> bool:
    if not needle:
        return False
    return needle.lower() in entry_text(entry)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("decisions", help="decisions.json (produced by AI / human)")
    ap.add_argument("--clean", default=str(DEFAULT_CLEAN))
    ap.add_argument("--review", default=str(DEFAULT_REVIEW))
    args = ap.parse_args()

    decisions = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    accepts = decisions.get("accepts") or []
    manual_decisions = decisions.get("manual") or []
    noise_decisions = decisions.get("noise") or []

    clean_path = Path(args.clean)
    review_path = Path(args.review)

    rows = load_clean(clean_path)
    review = json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else []

    # 1) Add accepts to clean.txt; mark matched review entries for removal.
    accept_matches: set[int] = set()
    for a in accepts:
        tag = a["tag"]
        title = a["title"]
        doi = a.get("doi", "")
        rows.append((tag, title, doi))
        needle = a.get("match") or title
        for i, e in enumerate(review):
            if match_entry(e, needle):
                accept_matches.add(i)

    # 2) Noise: remove from review entirely.
    noise_matches: set[int] = set()
    for n in noise_decisions:
        needle = n["match"]
        for i, e in enumerate(review):
            if match_entry(e, needle):
                noise_matches.add(i)

    # 3) Manual: tag with a marker so it stands out.
    manual_marker_set: set[int] = set()
    manual_reasons: dict[int, str] = {}
    for m in manual_decisions:
        needle = m["match"]
        reason = m.get("reason") or "needs manual DOI lookup"
        for i, e in enumerate(review):
            if match_entry(e, needle):
                manual_marker_set.add(i)
                manual_reasons[i] = reason

    new_review = []
    for i, e in enumerate(review):
        if i in accept_matches or i in noise_matches:
            continue
        if i in manual_marker_set:
            e = dict(e)
            e["_manual"] = manual_reasons[i]
        new_review.append(e)
    # Surface manual ones first
    new_review.sort(key=lambda e: 0 if "_manual" in e else 1)

    write_clean(clean_path, rows)
    review_path.write_text(json.dumps(new_review, ensure_ascii=False, indent=2),
                           encoding="utf-8")

    print(f"applied {len(accepts)} accepts, {len(noise_decisions)} noise, "
          f"{len(manual_decisions)} manual")
    print(f"  clean.txt rows: {len(set(rows))}")
    print(f"  review.json remaining: {len(new_review)} "
          f"(of which {sum(1 for e in new_review if '_manual' in e)} are manual)")


if __name__ == "__main__":
    main()
