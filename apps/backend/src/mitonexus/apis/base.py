from __future__ import annotations

import asyncio
from abc import ABC
from time import perf_counter
from typing import Any, Self

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class BaseAPIClient(ABC):
    """Abstract base for external API clients with retry and rate limiting."""

    base_url: str
    rate_limit_per_second: float = 1.0

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._client_owned = client is None
        self._last_request_time = 0.0
        self._request_lock = asyncio.Lock()

    async def close(self) -> None:
        """Close the shared HTTP client when it is owned by this instance."""
        if self._client_owned:
            await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10), reraise=True)
    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        async with self._request_lock:
            await self._respect_rate_limit()
            response = await self._client.request(method, f"{self.base_url}{path}", **kwargs)
            self._last_request_time = perf_counter()
        response.raise_for_status()
        return response

    async def _respect_rate_limit(self) -> None:
        if self.rate_limit_per_second <= 0:
            return

        minimum_interval = 1.0 / self.rate_limit_per_second
        elapsed = perf_counter() - self._last_request_time
        if elapsed < minimum_interval:
            await asyncio.sleep(minimum_interval - elapsed)
