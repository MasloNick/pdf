"""Fast parallel fetcher using ThreadPoolExecutor.

Replaces sequential scraping with concurrent requests.
40 bank sites: ~5 min sequential → ~15 sec parallel.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

LOGGER = logging.getLogger(__name__)


def fetch_parallel(
    tasks: List[Tuple[str, Callable[..., Any], tuple]],
    max_workers: int = 10,
    timeout: int = 60,
) -> Tuple[List[Any], List[str]]:
    """Run multiple fetch tasks in parallel.

    *tasks* is a list of ``(name, callable, args)`` tuples.
    Returns ``(results, errors)``.

    Example::

        tasks = [
            ("ПриватБанк", scraper.scan_bank, (privatbank_config,)),
            ("Ощадбанк",   scraper.scan_bank, (oschadbank_config,)),
        ]
        results, errors = fetch_parallel(tasks, max_workers=10)
    """
    results: List[Any] = []
    errors: List[str] = []

    start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_name = {
            pool.submit(fn, *args): name
            for name, fn, args in tasks
        }
        for future in as_completed(future_to_name, timeout=timeout):
            name = future_to_name[future]
            try:
                result = future.result()
                if result:
                    if isinstance(result, list):
                        results.extend(result)
                    else:
                        results.append(result)
                LOGGER.info("✓ %s completed", name)
            except Exception as exc:
                msg = f"{name}: {exc}"
                errors.append(msg)
                LOGGER.warning("✗ %s failed: %s", name, exc)

    elapsed = time.time() - start
    LOGGER.info(
        "Parallel fetch: %d tasks, %d results, %d errors, %.1fs",
        len(tasks), len(results), len(errors), elapsed,
    )
    return results, errors


def scan_all_banks_parallel(
    bank_registry: list,
    scraper: Any,
    max_workers: int = 10,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Scan all banks in parallel using ThreadPoolExecutor."""
    tasks = [
        (config.short_name, scraper.scan_bank, (config,))
        for config in bank_registry
    ]
    return fetch_parallel(tasks, max_workers=max_workers)
