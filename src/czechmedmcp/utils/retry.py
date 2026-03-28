"""Async retry utility with exponential backoff."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def async_retry(
    fn: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    max_retries: int = 3,
    backoff_base: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    **kwargs: Any,
) -> T:
    """Call *fn* with retries and exponential backoff.

    Parameters
    ----------
    fn:
        Async callable to invoke.
    max_retries:
        Total number of attempts (including the first).
    backoff_base:
        Multiplier applied to *initial_delay* after each failure.
    initial_delay:
        Seconds to wait after the first failure.
    max_delay:
        Upper bound for the delay between retries.

    Returns the result of *fn* on success.
    Raises the last exception after all retries are exhausted.
    """
    last_exc: BaseException | None = None
    delay = initial_delay

    for attempt in range(1, max_retries + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt == max_retries:
                break
            logger.warning(
                "Retry %d/%d for %s failed: %s — "
                "retrying in %.1fs",
                attempt,
                max_retries,
                fn.__name__,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
            delay = min(delay * backoff_base, max_delay)

    raise last_exc  # type: ignore[misc]
