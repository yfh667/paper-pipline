"""Deterministic cleaner — turns a messy paperlist.txt into the clean format
the fetcher expects, plus a separate review.json for entries the script
couldn't resolve confidently.

Workflow:
    python clean_list.py path/to/messy.txt
        -> writes  output/paperlist_clean.txt
                   output/paperlist_review.json
                   output/clean.log

The clean output goes straight to the fetcher:
    python run.py output/paperlist_clean.txt

The review.json is where human / AI judgment kicks in:
    [{"title": "...", "reason": "no crossref match"},
     {"title": "...", "candidates": [{doi, title, score}, ...]},
     ...]
Resolve each one (pick the right candidate, or supply a DOI), then append the
chosen lines to paperlist_clean.txt and rerun the fetcher.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = PROJECT_ROOT / "output"

UA = "paper-fetcher/1.0 (mailto:noreply@example.com)"

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
URL_RE = re.compile(r"https?://\S+")
CN_RE = re.compile(r"[一-鿿]")
MD_HEADER_RE = re.compile(r"^\s*#+\s+")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
MD_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")

# DOI prefix -> short tag used in the clean list
DOI_TAG = {
    "10.1109/": "ieee",
    "10.1145/": "acm",
    "10.1016/": "elsevier",
    "10.1007/": "springer",
    "10.1002/": "wiley",
    "10.3389/": "frontiers",
    "10.3390/": "mdpi",
    "10.1117/": "spie",
    "10.1364/": "optica",
    "10.3233/": "ios-press",
    "10.34133/": "science-partner",
    "10.36227/": "techrxiv",
    "10.5555/": "acm",                # ACM digital library secondary prefix
}

# URL-domain -> tag (for raw URLs whose DOI we cannot extract)
URL_TAG = [
    (re.compile(r"dl\.acm\.org", re.I), "acm"),
    (re.compile(r"ieeexplore\.ieee\.org", re.I), "ieee"),
    (re.compile(r"sciencedirect\.com", re.I), "elsevier"),
    (re.compile(r"link\.springer\.com", re.I), "springer"),
    (re.compile(r"onlinelibrary\.wiley\.com", re.I), "wiley"),
    (re.compile(r"frontiersin\.org", re.I), "frontiers"),
    (re.compile(r"mdpi\.com", re.I), "mdpi"),
    (re.compile(r"arxiv\.org", re.I), "arxiv"),
    (re.compile(r"usenix\.org", re.I), "usenix"),
    (re.compile(r"readcube\.com", re.I), "readcube"),
    (re.compile(r"kluedo\.ub\.rptu\.de", re.I), "kluedo-rptu"),
    (re.compile(r"webofscience\.", re.I), "wos"),
]

# Domains we strip out as obvious noise (chat links, AI tool URLs, etc.)
URL_SKIP = re.compile(
    r"(chatgpt\.com|gemini\.google\.com|scholar\.google\.|chat\.com)", re.I
)


# ---------------------------------------------------------------------------
# Step 1: parse the messy file into raw candidates
# ---------------------------------------------------------------------------

def _strip_markdown(line: str) -> str:
    line = MD_LINK_RE.sub(r"\1", line)
    line = MD_BOLD_RE.sub(r"\1", line)
    line = re.sub(r"_([^_]+)_", r"\1", line)
    line = MD_HEADER_RE.sub("", line)
    return line


def _strip_chinese_suffix(text: str) -> str | None:
    """If `text` has a tail of Chinese annotations, drop them.

    Heuristic: find the first run of Chinese characters; keep everything
    before it. If the English part is too short, treat the whole line as
    Chinese annotation and drop it (return None).
    """
    m = CN_RE.search(text)
    if not m:
        return text.strip()
    head = text[: m.start()].strip()
    if len(head) < 10:
        return None
    return head


def _is_noise(line: str) -> bool:
    line = line.strip()
    if not line:
        return True
    if line.startswith(("cd ", "python ", "$ ", "> ", "//", "::")):
        return True
    if line in ("精读", "必看", "需要整理", "把..."):
        return True
    return False


def _paragraphs(text: str):
    para: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            if para:
                yield para
                para = []
        else:
            para.append(line)
    if para:
        yield para


def parse_messy(text: str):
    """Yield candidate dicts:
        {"kind": "doi",   "doi": <doi>}
        {"kind": "url",   "url": <url>}
        {"kind": "title", "title": <english title>}
    """
    seen_dois: set[str] = set()
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    def _emit_doi(doi: str):
        doi = re.sub(r"[)\].,;'\"!?]+$", "", doi)
        if doi not in seen_dois:
            seen_dois.add(doi)
            return {"kind": "doi", "doi": doi}
        return None

    def _emit_url(url: str):
        url = url.rstrip(".,);'\"")
        if URL_SKIP.search(url):
            return None
        if url not in seen_urls:
            seen_urls.add(url)
            return {"kind": "url", "url": url}
        return None

    for para in _paragraphs(text):
        joined = "\n".join(para)

        # 1) URLs in any line of the paragraph
        for u in URL_RE.findall(joined):
            dm = DOI_RE.search(u)
            if dm:
                ev = _emit_doi(dm.group())
                if ev:
                    yield ev
            else:
                ev = _emit_url(u)
                if ev:
                    yield ev

        # 2) Build the title text from non-URL, markdown-stripped lines
        text_lines: list[str] = []
        for line in para:
            line = URL_RE.sub("", line)
            line = _strip_markdown(line).strip()
            if _is_noise(line):
                continue
            text_lines.append(line)
        if not text_lines:
            continue
        title = " ".join(text_lines).strip()

        # 3) DOI literal embedded in the prose? Emit and stop here.
        dm = DOI_RE.search(title)
        if dm:
            ev = _emit_doi(dm.group())
            if ev:
                yield ev
            continue

        # 4) Strip trailing Chinese annotations; skip if effectively Chinese-only
        stripped = _strip_chinese_suffix(title)
        if not stripped or len(stripped) < 15:
            continue
        norm = stripped.lower()
        if norm in seen_titles:
            continue
        seen_titles.add(norm)
        yield {"kind": "title", "title": stripped}


# ---------------------------------------------------------------------------
# Step 2: CrossRef lookups
# ---------------------------------------------------------------------------

_session = requests.Session()
_session.headers.update({"User-Agent": UA})


def crossref_lookup_doi(doi: str, timeout: int = 10) -> dict | None:
    try:
        r = _session.get(f"https://api.crossref.org/works/{doi}",
                         timeout=timeout)
        if r.status_code != 200:
            return None
        m = r.json().get("message", {})
        return {
            "doi": m.get("DOI", doi),
            "title": " ".join(m.get("title") or []) or "",
            "publisher": m.get("publisher", ""),
        }
    except Exception:
        return None


def crossref_search_title(title: str, rows: int = 3, timeout: int = 15) -> list[dict]:
    try:
        r = _session.get("https://api.crossref.org/works",
                         params={"query.title": title, "rows": rows},
                         timeout=timeout)
        r.raise_for_status()
    except Exception:
        return []
    items = r.json().get("message", {}).get("items", [])
    out = []
    for it in items:
        out.append({
            "doi": it.get("DOI", ""),
            "title": " ".join(it.get("title") or []),
            "publisher": it.get("publisher", ""),
            "score": it.get("score", 0),
        })
    return out


def title_similarity(query: str, found: str) -> float:
    q = query.lower().strip()
    f = found.lower().strip()
    if not q or not f:
        return 0.0
    if q == f:
        return 1.0
    if q in f or f in q:
        return 0.95
    qw = set(re.findall(r"[a-z0-9]+", q))
    fw = set(re.findall(r"[a-z0-9]+", f))
    if not qw or not fw:
        return 0.0
    inter = qw & fw
    return len(inter) / max(len(qw), len(fw))


def resolve_title(title: str, candidates: list[dict]) -> tuple[dict | None, float]:
    """Pick best candidate above confidence threshold. Returns (chosen, score)
    or (None, top_score) if ambiguous / low confidence."""
    if not candidates:
        return None, 0.0
    scored = []
    for c in candidates:
        s = title_similarity(title, c["title"])
        scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    top_score, top = scored[0]
    if top_score >= 0.85:
        # And not too close to runner-up
        if len(scored) > 1 and scored[1][0] >= top_score - 0.05 and top_score < 0.95:
            return None, top_score
        return top, top_score
    return None, top_score


# ---------------------------------------------------------------------------
# Step 3: tag classification
# ---------------------------------------------------------------------------

def classify_doi(doi: str, publisher: str = "") -> str:
    for prefix, tag in DOI_TAG.items():
        if doi.startswith(prefix):
            return tag
    if publisher:
        low = publisher.lower()
        if "ieee" in low: return "ieee"
        if "elsevier" in low: return "elsevier"
        if "acm" in low or "association for computing" in low: return "acm"
        if "springer" in low: return "springer"
        if "wiley" in low: return "wiley"
    return "unknown"


def classify_url(url: str) -> str | None:
    for pat, tag in URL_TAG:
        if pat.search(url):
            return tag
    return None


# ---------------------------------------------------------------------------
# Step 4: top-level pipeline
# ---------------------------------------------------------------------------

def clean(input_path: Path, out_clean: Path, out_review: Path,
          out_log: Path, use_crossref: bool = True,
          crossref_gap_sec: float = 1.0) -> None:
    text = input_path.read_text(encoding="utf-8")

    log_lines: list[str] = []
    def log(msg: str):
        log_lines.append(msg)
        print(msg)

    log(f"input: {input_path}  ({len(text)} bytes)")

    rows: list[tuple[str, str, str]] = []   # (tag, title, doi)
    review: list[dict] = []

    candidates = list(parse_messy(text))
    log(f"parsed candidates: {len(candidates)}")

    n_doi = sum(1 for c in candidates if c["kind"] == "doi")
    n_url = sum(1 for c in candidates if c["kind"] == "url")
    n_title = sum(1 for c in candidates if c["kind"] == "title")
    log(f"  by kind: doi={n_doi}  url={n_url}  title={n_title}")

    # --- DOIs: enrich with title + publisher via CrossRef
    for i, c in enumerate(candidates):
        if c["kind"] != "doi":
            continue
        doi = c["doi"]
        title = doi
        publisher = ""
        if use_crossref:
            meta = crossref_lookup_doi(doi)
            if meta:
                title = meta["title"] or doi
                publisher = meta["publisher"]
            time.sleep(crossref_gap_sec)
        tag = classify_doi(doi, publisher)
        rows.append((tag, title, doi))

    # --- URLs: classify by domain; we can't get a title for these here
    for c in candidates:
        if c["kind"] != "url":
            continue
        url = c["url"]
        tag = classify_url(url)
        if tag is None:
            review.append({"kind": "url", "url": url, "reason": "unknown domain"})
            continue
        rows.append((tag, url, ""))

    # --- Titles: CrossRef search; high-confidence -> accept, else -> review
    for c in candidates:
        if c["kind"] != "title":
            continue
        title = c["title"]
        if not use_crossref:
            review.append({"kind": "title", "title": title,
                           "reason": "crossref disabled"})
            continue
        log(f"  crossref search: {title[:70]}")
        cands = crossref_search_title(title)
        time.sleep(crossref_gap_sec)
        chosen, score = resolve_title(title, cands)
        if chosen:
            tag = classify_doi(chosen["doi"], chosen["publisher"])
            rows.append((tag, chosen["title"] or title, chosen["doi"]))
        else:
            review.append({
                "kind": "title",
                "title": title,
                "top_score": round(score, 3),
                "candidates": [
                    {"doi": x["doi"], "title": x["title"],
                     "publisher": x["publisher"], "score": x["score"]}
                    for x in cands[:3]
                ],
            })

    # --- Dedupe + sort
    seen_keys: set[tuple[str, str]] = set()
    unique: list[tuple[str, str, str]] = []
    for tag, title, doi in rows:
        key = (tag, doi or title.lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique.append((tag, title, doi))
    unique.sort(key=lambda r: (r[0], r[1].lower()))

    # --- Write outputs
    out_clean.parent.mkdir(parents=True, exist_ok=True)
    out_clean.write_text(
        "\n".join(f"[{t}] {title}  (doi={doi})" for t, title, doi in unique) + "\n",
        encoding="utf-8",
    )
    out_review.parent.mkdir(parents=True, exist_ok=True)
    out_review.write_text(json.dumps(review, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    tags = Counter(t for t, _, _ in unique)
    log("")
    log(f"wrote {len(unique)} clean rows -> {out_clean}")
    for t, n in sorted(tags.items(), key=lambda x: -x[1]):
        log(f"  {n:3d}  {t}")
    log(f"wrote {len(review)} review entries -> {out_review}")

    out_log.parent.mkdir(parents=True, exist_ok=True)
    out_log.write_text("\n".join(log_lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", help="messy paperlist.txt")
    ap.add_argument("--out", default=str(OUTPUT_ROOT / "paperlist_clean.txt"))
    ap.add_argument("--review", default=str(OUTPUT_ROOT / "paperlist_review.json"))
    ap.add_argument("--log", default=str(OUTPUT_ROOT / "clean.log"))
    ap.add_argument("--no-crossref", action="store_true",
                    help="skip CrossRef calls (titles -> review.json)")
    ap.add_argument("--crossref-gap", type=float, default=1.0,
                    help="seconds to sleep between CrossRef calls")
    args = ap.parse_args()
    clean(
        Path(args.input).resolve(),
        Path(args.out).resolve(),
        Path(args.review).resolve(),
        Path(args.log).resolve(),
        use_crossref=not args.no_crossref,
        crossref_gap_sec=args.crossref_gap,
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
