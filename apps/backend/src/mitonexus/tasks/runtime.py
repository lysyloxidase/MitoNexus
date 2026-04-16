from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any

_loop_state = threading.local()


def _get_worker_event_loop() -> asyncio.AbstractEventLoop:
    loop = getattr(_loop_state, "event_loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _loop_state.event_loop = loop
    return loop


def run_async_in_worker[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run async code on a persistent per-thread event loop.

    Celery tasks are synchronous, but the backend relies heavily on async SQLAlchemy
    and async LangGraph components. Reusing one loop per worker thread prevents
    asyncpg/SQLAlchemy resources from being rebound across fresh `asyncio.run(...)`
    calls in the same process.
    """

    loop = _get_worker_event_loop()
    if loop.is_running():
        msg = "Worker event loop is already running unexpectedly."
        raise RuntimeError(msg)

    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
