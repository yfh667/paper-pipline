"""Async dispatcher: group jobs by publisher tag, start one worker coroutine
per group, run them in parallel; within each worker the jobs are processed
serially with a politeness gap."""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from handlers import REGISTRY, Job, PublisherHandler


@dataclass
class JobResult:
    job: Job
    ok: bool
    path: Path | None = None
    error: str | None = None
    seconds: float = 0.0


async def _run_publisher(
    tag: str,
    jobs: list[Job],
    logger: logging.Logger,
    results: list[JobResult],
) -> None:
    cls = REGISTRY.get(tag)
    if cls is None:
        for j in jobs:
            results.append(JobResult(j, False, error=f"no handler for tag {tag!r}"))
        return

    handler: PublisherHandler = cls(out_dir=jobs[0].out_dir, logger=logger)
    try:
        await handler.setup()
    except Exception as e:
        logger.exception("[%s] setup failed", tag)
        for j in jobs:
            results.append(JobResult(j, False, error=f"setup: {e}"))
        return

    try:
        for i, job in enumerate(jobs, 1):
            logger.info("[%s] (%d/%d) %s", tag, i, len(jobs), job.doi)
            loop = asyncio.get_event_loop()
            t0 = loop.time()
            try:
                path = await handler.fetch_one(job)
                results.append(JobResult(job, True, path=path,
                                         seconds=loop.time() - t0))
            except Exception as e:
                logger.error("[%s] FAIL %s: %s", tag, job.doi, e)
                results.append(JobResult(job, False, error=str(e),
                                         seconds=loop.time() - t0))
            if i < len(jobs):
                await asyncio.sleep(handler.gap_seconds)
    finally:
        try:
            await handler.teardown()
        except Exception:
            logger.exception("[%s] teardown failed", tag)


async def run_jobs(
    jobs: Iterable[Job],
    logger: logging.Logger,
) -> list[JobResult]:
    """Group by tag, spawn one worker per group, gather results."""
    by_tag: dict[str, list[Job]] = defaultdict(list)
    for j in jobs:
        by_tag[j.tag].append(j)

    results: list[JobResult] = []
    tasks = [
        asyncio.create_task(_run_publisher(tag, group, logger, results),
                            name=f"publisher:{tag}")
        for tag, group in by_tag.items()
    ]
    if tasks:
        await asyncio.gather(*tasks)
    return results
