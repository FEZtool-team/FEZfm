"""Earthquake sources. Each module exposes ``fetch(client, start, end) -> list[Report]``."""

from __future__ import annotations

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


def iso(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
