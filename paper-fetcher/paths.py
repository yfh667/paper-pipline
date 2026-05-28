"""Path resolution for paper-fetcher.

Loads config.json (committed defaults) then merges config.local.json (per-machine
override, gitignored). CLI flags can override individual paths.

All scripts go through get_paths() so changing config.json (or passing CLI flags)
moves every output location at once.
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
LOCAL_CONFIG_PATH = PROJECT_ROOT / "config.local.json"


def load_config() -> dict:
    cfg: dict = {}
    if CONFIG_PATH.exists():
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    if LOCAL_CONFIG_PATH.exists():
        cfg.update(json.loads(LOCAL_CONFIG_PATH.read_text(encoding="utf-8")))
    return cfg


def _resolve(path_str: str) -> Path:
    """Resolve a path: absolute paths used as-is, relative paths anchored at PROJECT_ROOT."""
    p = Path(path_str)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


class Paths:
    """Derived paths. All output_* live under output_dir; input_dir is the messy-txt drop."""

    def __init__(self, cfg: dict | None = None,
                 input_dir: str | None = None,
                 output_dir: str | None = None):
        cfg = cfg or load_config()
        in_val = input_dir or cfg.get("input_dir", "./input")
        out_val = output_dir or cfg.get("output_dir", "./output")
        self.input_dir = _resolve(in_val)
        self.output_dir = _resolve(out_val)

    # publisher output dirs
    @property
    def ieee_dir(self) -> Path: return self.output_dir / "ieee"

    @property
    def acm_dir(self) -> Path: return self.output_dir / "acm"

    @property
    def sd_dir(self) -> Path: return self.output_dir / "sd"

    @property
    def optica_dir(self) -> Path: return self.output_dir / "optica"

    @property
    def publisher_dirs(self) -> dict[str, Path]:
        return {
            "ieee": self.ieee_dir,
            "acm": self.acm_dir,
            "elsevier": self.sd_dir,
            "optica": self.optica_dir,
        }

    # workflow files
    @property
    def paperlist_clean(self) -> Path: return self.output_dir / "paperlist_clean.txt"

    @property
    def paperlist_review(self) -> Path: return self.output_dir / "paperlist_review.json"

    @property
    def clean_log(self) -> Path: return self.output_dir / "clean.log"

    @property
    def manual_file(self) -> Path: return self.output_dir / "manual" / "needs_manual.txt"

    @property
    def log_dir(self) -> Path: return self.output_dir / "logs"

    @property
    def zotero_import_log(self) -> Path: return self.output_dir / "logs" / "zotero_import.log"

    # handler download scratch dirs (tmp during browser-based downloads)
    @property
    def acm_dl_tmp(self) -> Path: return self.output_dir / "_acm_dl_tmp"

    @property
    def optica_dl_tmp(self) -> Path: return self.output_dir / "_optica_dl_tmp"


def get_paths(input_dir: str | None = None,
              output_dir: str | None = None) -> Paths:
    return Paths(load_config(), input_dir, output_dir)


def add_path_args(parser) -> None:
    """Inject --input-dir / --output-dir into an argparse parser."""
    parser.add_argument(
        "--input-dir", default=None,
        help="Override input_dir from config.json (where messy.txt lives)",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output_dir from config.json (where PDFs/intermediate files go)",
    )
