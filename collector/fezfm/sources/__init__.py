"""Earthquake sources. Each module exposes ``fetch(client, start, end) -> list[Report]``."""

from __future__ import annotations

import httpx

USER_AGENT = "FEZfm/0.1 (+https://github.com/FEZtool-team/FEZfm)"


def make_client(timeout: float = 60.0) -> httpx.Client:
    transport = httpx.HTTPTransport(retries=2)
    return httpx.Client(
        timeout=timeout,
        transport=transport,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )


def iso(dt) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")
