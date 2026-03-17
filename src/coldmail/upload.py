from __future__ import annotations

import click
import httpx

from coldmail.config import INSTANTLY_API_BASE, INSTANTLY_API_KEY


def list_campaigns() -> list[dict]:
    """List all campaigns from Instantly."""
    resp = httpx.get(
        f"{INSTANTLY_API_BASE}/campaigns",
        headers={"Authorization": f"Bearer {INSTANTLY_API_KEY}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("items", resp.json() if isinstance(resp.json(), list) else [])


def upload_leads(campaign_id: str, leads: list[dict], batch_size: int = 100) -> int:
    """Upload leads to an Instantly campaign in batches. Returns count uploaded."""
    total_uploaded = 0
    for i in range(0, len(leads), batch_size):
        batch = leads[i : i + batch_size]
        payload = {
            "campaign_id": campaign_id,
            "leads": [
                {
                    "email": lead["email"],
                    "first_name": lead.get("first_name") or "",
                    "last_name": lead.get("last_name") or "",
                    "company_name": lead.get("company_name") or "",
                }
                for lead in batch
            ],
        }
        try:
            resp = httpx.post(
                f"{INSTANTLY_API_BASE}/leads",
                json=payload,
                headers={"Authorization": f"Bearer {INSTANTLY_API_KEY}"},
                timeout=30,
            )
            resp.raise_for_status()
            total_uploaded += len(batch)
            click.echo(f"  Uploaded batch {i // batch_size + 1} ({len(batch)} leads)")
        except httpx.HTTPError as e:
            click.echo(f"  Error uploading batch {i // batch_size + 1}: {e}")
    return total_uploaded
