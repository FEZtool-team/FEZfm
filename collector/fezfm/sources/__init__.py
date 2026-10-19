"""Earthquake sources. Each module exposes ``fetch(client, start, end) -> list[Report]``."""

from __future__ import annotations

import time

import httpx

USER_AGENT = "FEZfm/0.1 (+https://github.com/FEZtool-team/FEZfm)"


def make_client() -> httpx.Client:
    # Fail fast on servers that drop connections (connect 10 s, x3 with retries)
    # but allow slow responses for large catalog queries (45 s between bytes).
    transport = httpx.HTTPTransport(retries=2)
    return httpx.Client(
        timeout=httpx.Timeout(45.0, connect=10.0),
        transport=transport,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )


# Gateway errors that usually clear on a second try: USGS answers a query it has
# not cached in about 15 s, and its gateway sometimes gives up first (502).
RETRY_STATUS = {502, 503, 504}
RETRY_WAITS = (5, 20)  # seconds before the second and third try


def get(client: httpx.Client, url: str, params: dict, waits: tuple[float, ...] = RETRY_WAITS) -> httpx.Response:
    """GET with retries on gateway errors; any other status is returned as is."""
    for wait in (*waits, None):
        r = client.get(url, params=params)
        if r.status_code not in RETRY_STATUS or wait is None:
            return r
        time.sleep(wait)
    return r


def iso(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
