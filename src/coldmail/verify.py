from __future__ import annotations

import time

import click
import httpx

from coldmail.config import MILLION_VERIFIER_API_BASE, MILLION_VERIFIER_API_KEY


def verify_email(email: str) -> str:
    """Verify a single email via Million Verifier API. Returns result status."""
    resp = httpx.get(
        MILLION_VERIFIER_API_BASE,
        params={"api": MILLION_VERIFIER_API_KEY, "email": email},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("result", "unknown")


def verify_batch(leads: list[dict], delay: float = 0.5) -> list[tuple[str, str]]:
    """Verify a batch of leads. Returns list of (email, status) tuples."""
    results: list[tuple[str, str]] = []
    for i, lead in enumerate(leads):
        email = lead["email"]
        try:
            status = verify_email(email)
            results.append((email, status))
            click.echo(f"  [{i + 1}/{len(leads)}] {email} -> {status}")
        except httpx.HTTPError as e:
            results.append((email, "error"))
            click.echo(f"  [{i + 1}/{len(leads)}] {email} -> error: {e}")
        if i < len(leads) - 1:
            time.sleep(delay)
    return results
