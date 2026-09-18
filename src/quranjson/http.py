"""Rate-limited, retrying HTTP client for upstream snapshot fetches.

Upstreams are free community services. We identify ourselves, serialize requests at a
polite interval, and retry transient failures with backoff -- never hammering a host.
"""

from __future__ import annotations

import time
from typing import Any, Final

import httpx
import orjson
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from . import __version__

__all__ = ["Fetcher", "RetryableStatus"]

USER_AGENT: Final = f"quran-json/{__version__} (+https://github.com/risan/quran-json)"

#: Statuses worth retrying: throttling and transient upstream failure.
_RETRY_STATUS: Final = frozenset({408, 425, 429, 500, 502, 503, 504})


class RetryableStatus(Exception):
    """Upstream returned a status that is worth retrying."""

    def __init__(self, status: int, url: str) -> None:
        super().__init__(f"HTTP {status} from {url}")
        self.status = status


class Fetcher:
    """Blocking HTTP client with politeness delay and bounded retries."""

    def __init__(
        self,
        *,
        delay: float = 1.0,
        timeout: float = 60.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.delay = delay
        self._owns_client = client is None
        self._client = client or httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"},
        )
        self._last_request: float = 0.0

    def __enter__(self) -> Fetcher:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request = time.monotonic()

    @retry(
        retry=retry_if_exception_type((RetryableStatus, httpx.TransportError)),
        stop=stop_after_attempt(5),
        wait=wait_exponential_jitter(initial=2, max=60),
        reraise=True,
    )
    def get_bytes(self, url: str, *, headers: dict[str, str] | None = None) -> bytes:
        """Fetch ``url`` and return the raw body, retrying transient failures."""
        self._throttle()
        response = self._client.get(url, headers=headers)

        if response.status_code in _RETRY_STATUS:
            raise RetryableStatus(response.status_code, url)
        response.raise_for_status()

        return response.content

    def get_json(self, url: str) -> Any:
        """Fetch ``url`` and decode the body as JSON."""
        return orjson.loads(self.get_bytes(url))

    def head(self, url: str) -> httpx.Response:
        """Issue a HEAD request, retrying transient failures. Used for availability probes."""
        self._throttle()
        response = self._client.head(url)

        if response.status_code in _RETRY_STATUS:
            raise RetryableStatus(response.status_code, url)

        return response
