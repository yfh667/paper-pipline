"""Web-of-Science-style advanced-search GUI for exporting Zotero mineru MDs.

Each filter row is: [AND/OR] [Field] [Value]. Add as many rows as you want.
Within a field, you can stack multiple rows with the same field to OR/AND
together (e.g. Tag=A OR Tag=B AND Collection=routing).

Evaluation: standard precedence — AND binds tighter than OR. Rows joined by
AND form a group; OR splits into groups; an item matches if any group's
ANDs all pass.

Run:
  C:\\ProgramData\\miniconda3\\envs\\mineru\\pythonw.exe export_gui.py
"""
from __future__ import annotations

import functools
import json
import os
import shutil
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

sys.path.insert(0, str(Path(__file__).parent))
from zotero_query import load_index  # noqa: E402
from export_md import copy_flat, copy_perdoc  # noqa: E402

CONFIG_FILE = Path(__file__).with_name("config.json")
CONFIG = json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {}
MIRROR_ROOT = Path(CONFIG.get("mirror_dir", r"C:\Users\Administrator\Zotero\mineru-mirror"))
DEFAULT_INDEX = Path(CONFIG.get("index_file", str(MIRROR_ROOT / "index.json")))
STATE_FILE = Path(CONFIG.get("state_file", str(Path(__file__).with_name("state.json"))))


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _synthesize_orphan_items(idx: dict) -> list[dict]:
    """Build placeholder item records for MDs on disk whose attachment isn't in the index.

    Lets full-text / file-based searches still find them. Title/collection/tag
    filters will naturally exclude these (they have no metadata).
    """
    state = _load_state()
    keys_in_index: set[str] = set()
    for it in idx.get("items", {}).values():
        for a in it.get("attachments") or []:
            if a.get("key"):
                keys_in_index.add(a["key"])
    out: list[dict] = []
    for ak, info in state.items():
        if ak in keys_in_index:
            continue
        if info.get("status") != "ok":
            continue
        md_path = info.get("md_path")
        if not md_path or not Path(md_path).exists():
            continue
        pdf_path = info.get("pdf_path", "") or ""
        pdf_stem = Path(pdf_path).stem if pdf_path else ak
        out.append({
            "key": f"orphan-{ak}",
            "itemType": "orphan-attachment",
            "title": f"(uncategorized) {pdf_stem}",
            "creators": [],
            "year": None,
            "tags": [],
            "collections": [],
            "abstract": "",
            "attachments": [{
                "key": ak,
                "title": pdf_stem,
                "content_type": "application/pdf",
                "mineru_status": "ok",
                "md_path": md_path,
                "page_count": info.get("page_count"),
            }],
            "notes": [],
        })
    return out


def _refresh_md_status(idx: dict) -> tuple[int, int]:
    """Overlay current state.json onto the in-memory index.

    Returns (updated, orphan_mds) where:
      updated     = number of attachments whose mineru_status/md_path changed
      orphan_mds  = MDs on disk whose attachment key isn't in the index at all
                    (means user added new PDFs after last index build).
    """
    state = _load_state()
    keys_in_index: set[str] = set()
    updated = 0
    for it in idx.get("items", {}).values():
        for a in it.get("attachments") or []:
            ak = a.get("key")
            if ak:
                keys_in_index.add(ak)
            s = state.get(ak) if ak else None
            if not s:
                continue
            new_status = s.get("status")
            new_path = s.get("md_path")
            if a.get("mineru_status") != new_status or a.get("md_path") != new_path:
                a["mineru_status"] = new_status
                a["md_path"] = new_path
                if s.get("page_count") is not None:
                    a["page_count"] = s.get("page_count")
                updated += 1

    # Detect orphan MDs on disk (attachments that exist in mirror but not in index).
    orphan_mds = 0
    if MIRROR_ROOT.exists():
        for sub in MIRROR_ROOT.iterdir():
            if not sub.is_dir():
                continue
            if len(sub.name) != 8:
                continue
            if sub.name in keys_in_index:
                continue
            if any(sub.rglob("*.md")):
                orphan_mds += 1
    return updated, orphan_mds

# Fields the user can pick. The right-hand side is (canonical_op, takes_combobox).
FIELDS: dict[str, dict] = {
    "Tag (exact)":        {"id": "tag_exact",     "combo": True},
    "Tag (contains)":     {"id": "tag_contains",  "combo": True},
    "Collection":         {"id": "collection",    "combo": True},
    "Title contains":     {"id": "title",         "combo": False},
    "Abstract contains":  {"id": "abstract",      "combo": False},
    "Title or Abstract":  {"id": "title_or_abs",  "combo": False},
    "Author":             {"id": "author",        "combo": False},
    "Full text contains": {"id": "fulltext",      "combo": False},
    "Year >=":            {"id": "year_min",      "combo": False},
    "Year <=":            {"id": "year_max",      "combo": False},
    "Year =":             {"id": "year_eq",       "combo": False},
}


@functools.lru_cache(maxsize=4096)
def _read_md_cached(path: str) -> str:
    """Read an MD file once and cache its lowercased content for fast substring search."""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return ""


def _item_md_paths(item: dict) -> list[str]:
    return [
        a["md_path"]
        for a in (item.get("attachments") or [])
        if a.get("mineru_status") == "ok" and a.get("md_path")
    ]
FIELD_LABELS = list(FIELDS.keys())


# --------------------------------------------------------------------------
# Filter rule evaluation
# --------------------------------------------------------------------------

def _norm(s: str | None) -> str:
    return (s or "").lower()


def _item_authors_blob(item: dict) -> str:
    return " ".join(
        f"{(c.get('lastName') or '')} {(c.get('firstName') or '')}"
        for c in (item.get("creators") or [])
    ).lower()


def _matches_collection(item: dict, value: str, idx: dict) -> bool:
    v = value.lower()
    coll_keys = set(item.get("collections") or [])
    for ck in coll_keys:
        c = idx["collections"].get(ck)
        if not c:
            continue
        if v in (c.get("name") or "").lower() or v in (c.get("path") or "").lower():
            return True
    return False


def evaluate_row(item: dict, field_id: str, value: str, idx: dict) -> bool:
    if not value.strip():
        # Empty rule = matches everything (treated as no constraint).
        return True
    v = value.strip()
    if field_id == "tag_exact":
        return any((t or "").lower() == v.lower() for t in item.get("tags") or [])
    if field_id == "tag_contains":
        return any(v.lower() in (t or "").lower() for t in item.get("tags") or [])
    if field_id == "collection":
        return _matches_collection(item, v, idx)
    if field_id == "title":
        return v.lower() in (item.get("title") or "").lower()
    if field_id == "abstract":
        return v.lower() in (item.get("abstract") or "").lower()
    if field_id == "title_or_abs":
        return v.lower() in (item.get("title") or "").lower() or v.lower() in (item.get("abstract") or "").lower()
    if field_id == "author":
        return v.lower() in _item_authors_blob(item)
    if field_id == "fulltext":
        needle = v.lower()
        for p in _item_md_paths(item):
            if needle in _read_md_cached(p):
                return True
        return False
    if field_id in ("year_min", "year_max", "year_eq"):
        try:
            yv = int(v)
        except ValueError:
            return False
        iy = item.get("year")
        if iy is None:
            return False
        if field_id == "year_min": return iy >= yv
        if field_id == "year_max": return iy <= yv
        if field_id == "year_eq":  return iy == yv
    return False


def filter_with_rules(items: list[dict], rules: list[dict], idx: dict) -> list[dict]:
    """rules: list of {"combine": "AND"|"OR", "field_id": str, "value": str}.
    First row's 'combine' is ignored. AND binds tighter than OR.
    Implementation: split into OR-groups; within group, every rule must pass.
    """
    if not rules:
        return list(items)

    # Build OR-groups: a row with combine=="OR" starts a new group.
    groups: list[list[dict]] = []
    current: list[dict] = []
    for i, r in enumerate(rules):
        if i == 0 or r.get("combine", "AND") == "AND":
            current.append(r)
        else:  # OR
            if current:
                groups.append(current)
            current = [r]
    if current:
        groups.append(current)

    def passes(item):
        for grp in groups:
            if all(evaluate_row(item, r["field_id"], r["value"], idx) for r in grp):
                return True
        return False

    return [it for it in items if passes(it)]


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

class FilterRow:
    """One advanced-search row. Owned by the GUI's filter container."""
    def __init__(self, parent: ttk.Frame, app: "ExportApp", is_first: bool):
        self.app = app
        self.frame = ttk.Frame(parent)
        self.combine_var = tk.StringVar(value="AND")
        self.field_var = tk.StringVar(value=FIELD_LABELS[0])
        self.value_var = tk.StringVar()

        self.combine_cb = ttk.Combobox(self.frame, textvariable=self.combine_var,
                                       values=["AND", "OR"], width=5, state="readonly")
        self.field_cb = ttk.Combobox(self.frame, textvariable=self.field_var,
                                     values=FIELD_LABELS, width=20, state="readonly")
        self.value_cb = ttk.Combobox(self.frame, textvariable=self.value_var, width=44)
        self.remove_btn = ttk.Button(self.frame, text="–", width=3, command=self._on_remove)

        self.combine_cb.grid(row=0, column=0, padx=(0, 6))
        self.field_cb.grid(row=0, column=1, padx=(0, 6))
        self.value_cb.grid(row=0, column=2, padx=(0, 6), sticky="ew")
        self.remove_btn.grid(row=0, column=3)
        self.frame.columnconfigure(2, weight=1)

        if is_first:
            self.combine_cb.configure(state="disabled")

        self.field_cb.bind("<<ComboboxSelected>>", lambda _e: self._on_field_change())
        self._on_field_change()

    def _on_field_change(self):
        meta = FIELDS[self.field_var.get()]
        fid = meta["id"]
        if fid in ("tag_exact", "tag_contains"):
            self.value_cb.configure(values=[""] + self.app.tag_values)
        elif fid == "collection":
            self.value_cb.configure(values=[""] + self.app.collection_values)
        else:
            self.value_cb.configure(values=[])

    def _on_remove(self):
        self.app.remove_row(self)

    def to_rule(self) -> dict:
        return {
            "combine": self.combine_var.get(),
            "field_id": FIELDS[self.field_var.get()]["id"],
            "field_label": self.field_var.get(),
            "value": self.value_var.get().strip(),
        }


class ExportApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zotero -> Markdown Export (Advanced)")
        self.geometry("1080x780")
        self.minsize(900, 640)

        self._index_path = tk.StringVar(value=str(DEFAULT_INDEX))
        self._out_dir = tk.StringVar()
        self._layout = tk.StringVar(value="flat")
        self._with_images = tk.BooleanVar(value=False)
        self._clear = tk.BooleanVar(value=False)
        self._limit = tk.StringVar()

        self._index: dict | None = None
        self.tag_values: list[str] = []
        self.collection_values: list[str] = []
        self._rows: list[FilterRow] = []
        self._busy = False

        self._build_ui()
        self._add_initial_row()
        self._load_index_in_background()

    # ----- UI ---------------------------------------------------------------

    def _build_ui(self):
        try:
            ttk.Style().theme_use("vista")
        except tk.TclError:
            pass

        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)

        # Index row
        idx_frame = ttk.Frame(root)
        idx_frame.grid(row=0, column=0, sticky="ew")
        idx_frame.columnconfigure(1, weight=1)
        ttk.Label(idx_frame, text="Index file:").grid(row=0, column=0, sticky="w")
        ttk.Entry(idx_frame, textvariable=self._index_path).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(idx_frame, text="Browse...", command=self._pick_index).grid(row=0, column=2)
        ttk.Button(idx_frame, text="Reload", command=self._load_index_in_background).grid(row=0, column=3, padx=(6, 0))
        ttk.Button(idx_frame, text="Rebuild index", command=self._rebuild_index).grid(row=0, column=4, padx=(6, 0))

        # Filters area
        ttk.Separator(root, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=10)
        hdr = ttk.Frame(root)
        hdr.grid(row=2, column=0, sticky="ew")
        ttk.Label(hdr, text="Search rules", font=("", 10, "bold")).pack(side="left")
        ttk.Label(hdr, text="  (AND binds tighter than OR — within a row, blank value = no constraint)",
                  foreground="#555").pack(side="left")
        ttk.Button(hdr, text="+ Add rule", command=self._add_row).pack(side="right")

        self._rows_frame = ttk.Frame(root)
        self._rows_frame.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        self._rows_frame.columnconfigure(0, weight=1)

        # Other limit (post-filter)
        misc = ttk.Frame(root)
        misc.grid(row=4, column=0, sticky="w", pady=8)
        ttk.Label(misc, text="Limit result:").pack(side="left")
        ttk.Entry(misc, textvariable=self._limit, width=8).pack(side="left", padx=4)
        ttk.Label(misc, text="(0 = all)").pack(side="left", padx=(2, 0))

        # Output
        ttk.Separator(root, orient="horizontal").grid(row=5, column=0, sticky="ew", pady=10)
        ttk.Label(root, text="Output", font=("", 10, "bold")).grid(row=6, column=0, sticky="w")

        out_frame = ttk.Frame(root)
        out_frame.grid(row=7, column=0, sticky="ew", pady=(4, 0))
        out_frame.columnconfigure(1, weight=1)
        ttk.Label(out_frame, text="Output folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(out_frame, textvariable=self._out_dir).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(out_frame, text="Browse...", command=self._pick_outdir).grid(row=0, column=2)

        opt_frame = ttk.Frame(root)
        opt_frame.grid(row=8, column=0, sticky="w", pady=(6, 0))
        ttk.Label(opt_frame, text="Layout:").pack(side="left")
        ttk.Radiobutton(opt_frame, text="Flat", variable=self._layout, value="flat").pack(side="left", padx=(6, 0))
        ttk.Radiobutton(opt_frame, text="Per-doc (Obsidian-style)", variable=self._layout, value="perdoc").pack(side="left", padx=(6, 0))
        ttk.Checkbutton(opt_frame, text="Include images (perdoc only)", variable=self._with_images).pack(side="left", padx=(20, 0))
        ttk.Checkbutton(opt_frame, text="Clear output before export", variable=self._clear).pack(side="left", padx=(20, 0))

        # Action buttons
        act = ttk.Frame(root)
        act.grid(row=9, column=0, sticky="ew", pady=12)
        self._preview_btn = ttk.Button(act, text="Preview matches", command=self._on_preview)
        self._preview_btn.pack(side="left")
        self._export_btn = ttk.Button(act, text="Export now", command=self._on_export)
        self._export_btn.pack(side="left", padx=(8, 0))
        ttk.Button(act, text="Open output folder", command=self._open_outdir).pack(side="left", padx=(8, 0))
        ttk.Button(act, text="Clear log", command=self._clear_log).pack(side="right")

        # Log
        ttk.Label(root, text="Log", font=("", 10, "bold")).grid(row=10, column=0, sticky="w")
        root.rowconfigure(11, weight=1)
        self._log = scrolledtext.ScrolledText(root, height=16, wrap="none", font=("Consolas", 10))
        self._log.grid(row=11, column=0, sticky="nsew", pady=(4, 0))

        self._status = tk.StringVar(value="Ready.")
        ttk.Label(root, textvariable=self._status, anchor="w", relief="sunken", padding=4).grid(
            row=12, column=0, sticky="ew", pady=(8, 0)
        )

    # ----- filter row management -------------------------------------------

    def _add_initial_row(self):
        self._add_row()

    def _add_row(self):
        is_first = len(self._rows) == 0
        row = FilterRow(self._rows_frame, self, is_first=is_first)
        row.frame.grid(row=len(self._rows), column=0, sticky="ew", pady=2)
        # When more than one row, allow removing the first too.
        if not is_first:
            for r in self._rows:
                r.remove_btn.configure(state="normal")
        else:
            row.remove_btn.configure(state="disabled")
        self._rows.append(row)

    def remove_row(self, row: FilterRow):
        if len(self._rows) <= 1:
            return  # always keep at least one
        row.frame.destroy()
        self._rows.remove(row)
        # Re-grid + re-disable combine on the new first row.
        for i, r in enumerate(self._rows):
            r.frame.grid_configure(row=i)
            r.combine_cb.configure(state="disabled" if i == 0 else "readonly")
            r.remove_btn.configure(state="disabled" if len(self._rows) == 1 else "normal")

    # ----- index loading ----------------------------------------------------

    def _load_index_in_background(self):
        if self._busy:
            return
        p = Path(self._index_path.get())
        if not p.exists():
            self._log_line(f"Index not found: {p}")
            self._log_line("Click 'Rebuild index' to generate it.")
            self._status.set("Index missing")
            return
        self._set_busy(True, "Loading index...")
        def work():
            try:
                idx = load_index(p)
            except Exception as e:
                self.after(0, lambda: self._on_index_load_failed(e))
                return
            self.after(0, lambda: self._on_index_loaded(idx))
        threading.Thread(target=work, daemon=True).start()

    def _on_index_loaded(self, idx: dict):
        self._index = idx
        _read_md_cached.cache_clear()  # MD paths may have shifted; drop cached content
        updated, orphan = _refresh_md_status(self._index)
        if updated or orphan:
            self._log_line(f"Refreshed mineru status from state.json: {updated} attachment(s) updated, {orphan} orphan MD(s) on disk not in index")
            if orphan:
                self._log_line(f"  -> {orphan} MD(s) live in mirror but aren't in the index. Click 'Rebuild index' to expose them.")
        # Tags sorted by use frequency (descending), then alphabetical.
        tag_dict = idx.get("tags") or {}
        self.tag_values = sorted(tag_dict.keys(), key=lambda t: (-len(tag_dict[t]), t.lower()))
        coll_paths = sorted({
            (c.get("path") or c.get("name") or "")
            for c in (idx.get("collections") or {}).values()
        })
        self.collection_values = [p for p in coll_paths if p]
        for r in self._rows:
            r._on_field_change()
        summary = idx.get("summary", {})
        self._log_line(
            f"Loaded index: {summary.get('total_items_in_index')} items, "
            f"{summary.get('total_collections')} collections, "
            f"{summary.get('total_tags')} tags, "
            f"{summary.get('items_with_md')} have MD. "
            f"Generated: {idx.get('generated_at')}"
        )
        self._set_busy(False, "Ready.")

    def _on_index_load_failed(self, e: Exception):
        self._log_line(f"Failed to load index: {e}")
        self._set_busy(False, "Index load failed")

    def _rebuild_index(self):
        if self._busy:
            return
        self._set_busy(True, "Rebuilding index (~3-5 min)...")
        self._log_line(">> rebuilding index")
        def work():
            import subprocess
            cmd = [
                r"C:\ProgramData\miniconda3\envs\mineru\python.exe",
                str(Path(__file__).with_name("build_index.py")),
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
                out = (proc.stdout or "") + (proc.stderr or "")
                self.after(0, lambda: self._log_line(out.strip()))
                self.after(0, lambda: (self._set_busy(False, "Index rebuilt"), self._load_index_in_background()))
            except Exception as e:
                self.after(0, lambda: (self._log_line(f"Rebuild failed: {e}"), self._set_busy(False, "Rebuild failed")))
        threading.Thread(target=work, daemon=True).start()

    # ----- filter run -------------------------------------------------------

    def _collect_rules(self) -> list[dict]:
        rules = [r.to_rule() for r in self._rows]
        rules = [r for r in rules if r["value"]]
        return rules

    def _filtered(self) -> list[dict]:
        if not self._index:
            return []
        # Refresh from state.json each run so a long-running batch's progress
        # is visible without rebuilding the index.
        updated, orphan = _refresh_md_status(self._index)
        if updated:
            self._log_line(f"  (refreshed {updated} attachment(s) from state.json)")
        # Include MDs on disk whose attachment isn't in the index (newly imported
        # PDFs added after last index build) so file-based searches still see them.
        orphans = _synthesize_orphan_items(self._index)
        if orphans:
            self._log_line(f"  (including {len(orphans)} orphan MD(s); rebuild index for full metadata)")
        all_items = list(self._index["items"].values()) + orphans
        # Force has-md (no point exporting items without MD)
        all_items = [it for it in all_items
                     if any(a.get("mineru_status") == "ok" and a.get("md_path") for a in (it.get("attachments") or []))]
        rules = self._collect_rules()
        out = filter_with_rules(all_items, rules, self._index)
        try:
            lim = int(self._limit.get()) if self._limit.get().strip() else 0
        except ValueError:
            raise ValueError("Limit must be a number")
        if lim:
            out = out[:lim]
        return out

    def _on_preview(self):
        if not self._index:
            messagebox.showerror("No index", "Index is not loaded.")
            return
        try:
            matched = self._filtered()
        except ValueError as e:
            messagebox.showerror("Bad input", str(e)); return
        rules = self._collect_rules()
        self._log_line(f"-- Preview: rules={rules}")
        self._log_line(f"   {len(matched)} match(es)")
        for it in matched[:200]:
            yr = it.get("year") or "?"
            title = (it.get("title") or "(no title)")[:80]
            tags = ", ".join(it.get("tags") or [])[:60]
            self._log_line(f"  [{it['key']}] {yr}  {title}  tags=[{tags}]")
        if len(matched) > 200:
            self._log_line(f"  ... and {len(matched) - 200} more")
        self._status.set(f"Preview: {len(matched)} match(es)")

    def _on_export(self):
        if self._busy:
            return
        if not self._index:
            messagebox.showerror("No index", "Index is not loaded.")
            return
        out_dir_str = self._out_dir.get().strip()
        if not out_dir_str:
            messagebox.showerror("Missing output", "Choose an output folder first.")
            return
        try:
            matched = self._filtered()
        except ValueError as e:
            messagebox.showerror("Bad input", str(e)); return
        if not matched:
            messagebox.showinfo("No matches", "No items matched the filter.")
            return
        rules = self._collect_rules()
        n = len(matched)
        if not messagebox.askyesno(
            "Confirm export",
            f"Export {n} item(s) to:\n{out_dir_str}\n\nLayout: {self._layout.get()}\n"
            f"Clear first: {self._clear.get()}\nWith images: {self._with_images.get()}",
        ):
            return

        out_dir = Path(out_dir_str)
        layout = self._layout.get()
        with_images = self._with_images.get()
        clear = self._clear.get()

        self._set_busy(True, f"Exporting {n} item(s)...")
        def work():
            try:
                if clear and out_dir.exists():
                    self.after(0, lambda: self._log_line(f"clearing existing {out_dir}"))
                    shutil.rmtree(out_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
                manifest: list[dict] = []
                exported = 0
                errors = 0
                for it in matched:
                    for att in it.get("attachments") or []:
                        if att.get("mineru_status") != "ok":
                            continue
                        md_path = att.get("md_path")
                        if not md_path:
                            continue
                        src_md = Path(md_path)
                        if not src_md.exists():
                            self.after(0, lambda k=it['key'], p=src_md:
                                self._log_line(f"  [{k}] WARN missing on disk: {p}"))
                            continue
                        try:
                            if layout == "flat":
                                rec = copy_flat(it, att, src_md, out_dir, self._index)
                            else:
                                rec = copy_perdoc(it, att, src_md, out_dir, self._index, with_images)
                            manifest.append(rec)
                            exported += 1
                            self.after(0, lambda k=it['key'], r=rec:
                                self._log_line(f"  [{k}] -> {r.get('exported_md')}"))
                        except Exception as e:
                            errors += 1
                            self.after(0, lambda k=it['key'], msg=str(e):
                                self._log_line(f"  [{k}] ERROR: {msg}"))
                manifest_path = out_dir / "manifest.json"
                with manifest_path.open("w", encoding="utf-8") as f:
                    json.dump({
                        "exported_at": datetime.now().isoformat(timespec="seconds"),
                        "rules": rules,
                        "layout": layout,
                        "with_images": with_images,
                        "count": exported,
                        "items": manifest,
                    }, f, ensure_ascii=False, indent=2)
                self.after(0, lambda:
                    (self._log_line(f"Done. exported={exported} errors={errors}  manifest={manifest_path}"),
                     self._set_busy(False, f"Exported {exported} item(s)")))
            except Exception as e:
                self.after(0, lambda: (self._log_line(f"Export failed: {e}"), self._set_busy(False, "Export failed")))
        threading.Thread(target=work, daemon=True).start()

    # ----- helpers ----------------------------------------------------------

    def _pick_index(self):
        path = filedialog.askopenfilename(
            title="Select index.json",
            initialdir=str(Path(self._index_path.get()).parent if self._index_path.get() else Path.home()),
            filetypes=[("JSON files", "*.json"), ("All", "*.*")],
        )
        if path:
            self._index_path.set(path)
            self._load_index_in_background()

    def _pick_outdir(self):
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self._out_dir.set(path)

    def _open_outdir(self):
        path = self._out_dir.get().strip()
        if not path or not Path(path).exists():
            messagebox.showinfo("No folder", "Output folder does not exist yet.")
            return
        os.startfile(path)

    def _log_line(self, line: str):
        self._log.insert("end", line + "\n")
        self._log.see("end")

    def _clear_log(self):
        self._log.delete("1.0", "end")

    def _set_busy(self, busy: bool, status: str):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self._preview_btn.configure(state=state)
        self._export_btn.configure(state=state)
        self._status.set(status)
        self.configure(cursor="watch" if busy else "")


def main() -> int:
    app = ExportApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
