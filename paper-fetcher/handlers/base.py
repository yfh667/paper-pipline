"""Job model + abstract handler base class."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Job:
    doi: str
    title: str = ""
    tag: str = ""                                # short tag from input list: ieee/acm/elsevier
    out_dir: Path = field(default_factory=Path)  # publisher's output directory

    @property
    def safe_name(self) -> str:
        base = (self.title or self.doi.replace("/", "_"))
        base = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", base)
        base = re.sub(r"\s+", " ", base).strip()
        return (base[:140].rstrip() or "paper") + ".pdf"


class PublisherHandler:
    """Async handler base. fetch_one() calls are serialized per handler instance
    by the dispatcher; different handlers run in parallel."""

    tag: str = ""
    gap_seconds: int = 60

    def __init__(self, *, out_dir: Path, logger: logging.Logger):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.log = logger

    async def setup(self) -> None: ...
    async def teardown(self) -> None: ...

    async def fetch_one(self, job: Job) -> Path:
        raise NotImplementedError
