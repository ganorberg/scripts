from __future__ import annotations

from pathlib import Path

import click

from coldmail import db, ingest, spam_check, upload, verify
from coldmail.config import INSTANTLY_API_KEY, MILLION_VERIFIER_API_KEY


@click.group()
def cli():
    """Cold email automation pipeline."""
    pass


@cli.command("init-db")
def init_db_cmd():
    """Create the SQLite database and schema."""
    db.init_db()
    click.echo("Database initialized.")


@cli.command("ingest")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True), help="CSV file")
@click.option(
    "--source",
    required=True,
    type=click.Choice(["prospeo", "ocean", "discolike", "generic"]),
    help="Lead source (determines column mapping)",
)
@click.option("--campaign-id", required=True, help="Campaign identifier")
@click.option("--mapping", default=None, help="Custom column mapping JSON")
def ingest_cmd(file_path: str, source: str, campaign_id: str, mapping: str | None):
    """Ingest leads from a CSV file."""
    leads, warnings = ingest.parse_csv(Path(file_path), source, campaign_id, mapping)
    for w in warnings:
        click.echo(f"  Warning: {w}")

    if not leads:
        click.echo("No valid leads found.")
        return

    inserted, skipped = db.insert_leads(leads)
    click.echo(f"Ingested {inserted} leads, {skipped} duplicates skipped.")


@cli.command("verify")
@click.option("--limit", default=300, help="Max leads to verify")
@click.option("--delay", default=0.5, help="Seconds between API calls")
@click.option("--campaign-id", default=None, help="Filter by campaign")
def verify_cmd(limit: int, delay: float, campaign_id: str | None):
    """Verify emails via Million Verifier."""
    if not MILLION_VERIFIER_API_KEY:
        click.echo("Error: MILLION_VERIFIER_API_KEY not set in .env")
        return

    leads = db.get_unverified_leads(limit, campaign_id)
    if not leads:
        click.echo("No unverified leads found.")
        return

    click.echo(f"Verifying {len(leads)} leads...")
    results = verify.verify_batch(leads, delay)
    for email, status in results:
        db.update_verified_status(email, status)

    status_counts: dict[str, int] = {}
    for _, status in results:
        status_counts[status] = status_counts.get(status, 0) + 1
    summary = ", ".join(f"{s}: {c}" for s, c in sorted(status_counts.items()))
    click.echo(f"Verification complete. {summary}")


@cli.command("spam-check")
@click.option(
    "--file", "file_path", required=True, type=click.Path(exists=True), help="Email template file"
)
def spam_check_cmd(file_path: str):
    """Check an email template for spam trigger words."""
    text = Path(file_path).read_text()
    found = spam_check.check_spam(text)
    if not found:
        click.echo("You can safely send this email.")
    else:
        joined = '", "'.join(found)
        click.echo(
            f'The following spam words were detected: "{joined}". '
            f"Please remove them before sending."
        )


@cli.command("upload")
@click.option("--campaign-id", required=True, help="Instantly campaign ID")
def upload_cmd(campaign_id: str):
    """Upload verified leads to Instantly."""
    if not INSTANTLY_API_KEY:
        click.echo("Error: INSTANTLY_API_KEY not set in .env")
        return

    leads = db.get_uploadable_leads(campaign_id)
    if not leads:
        click.echo("No verified leads ready for upload.")
        return

    click.echo(f"Uploading {len(leads)} leads to Instantly...")
    count = upload.upload_leads(campaign_id, leads)
    if count > 0:
        db.mark_uploaded([lead["email"] for lead in leads[:count]])
    click.echo(f"Uploaded {count} leads to campaign {campaign_id}.")


@cli.command("campaigns")
def campaigns_cmd():
    """List Instantly campaigns."""
    if not INSTANTLY_API_KEY:
        click.echo("Error: INSTANTLY_API_KEY not set in .env")
        return

    campaigns = upload.list_campaigns()
    if not campaigns:
        click.echo("No campaigns found.")
        return

    for c in campaigns:
        name = c.get("name", "Unnamed")
        cid = c.get("id", "?")
        click.echo(f"  {name} ({cid})")


@cli.command("stats")
def stats_cmd():
    """Show database statistics."""
    s = db.get_stats()
    click.echo(f"Total leads: {s['total']}")
    click.echo("By verification status:")
    for status, count in s["by_status"].items():
        click.echo(f"  {status}: {count}")
    click.echo(f"Uploaded to Instantly: {s['uploaded']}")
    click.echo("By campaign:")
    for campaign, count in s["by_campaign"].items():
        click.echo(f"  {campaign}: {count}")


@cli.command("pipeline")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True), help="CSV file")
@click.option(
    "--source",
    required=True,
    type=click.Choice(["prospeo", "ocean", "discolike", "generic"]),
)
@click.option("--campaign-id", required=True, help="Campaign identifier")
@click.option("--mapping", default=None, help="Custom column mapping JSON")
@click.option("--verify-delay", default=0.5, help="Seconds between verify calls")
@click.option("--skip-verify", is_flag=True, help="Skip email verification")
@click.option("--skip-upload", is_flag=True, help="Skip Instantly upload")
def pipeline_cmd(
    file_path: str,
    source: str,
    campaign_id: str,
    mapping: str | None,
    verify_delay: float,
    skip_verify: bool,
    skip_upload: bool,
):
    """Run the full pipeline: ingest -> verify -> upload."""
    # Ingest
    click.echo("=== Ingesting leads ===")
    leads, warnings = ingest.parse_csv(Path(file_path), source, campaign_id, mapping)
    for w in warnings:
        click.echo(f"  Warning: {w}")
    if not leads:
        click.echo("No valid leads found. Stopping.")
        return
    inserted, skipped = db.insert_leads(leads)
    click.echo(f"Ingested {inserted} leads, {skipped} duplicates skipped.")

    # Verify
    if not skip_verify:
        if not MILLION_VERIFIER_API_KEY:
            click.echo("Warning: MILLION_VERIFIER_API_KEY not set, skipping verification.")
        else:
            click.echo("\n=== Verifying emails ===")
            unverified = db.get_unverified_leads(len(leads), campaign_id)
            if unverified:
                results = verify.verify_batch(unverified, verify_delay)
                for email, status in results:
                    db.update_verified_status(email, status)
                click.echo(f"Verified {len(results)} leads.")

    # Upload
    if not skip_upload:
        if not INSTANTLY_API_KEY:
            click.echo("Warning: INSTANTLY_API_KEY not set, skipping upload.")
        else:
            click.echo("\n=== Uploading to Instantly ===")
            uploadable = db.get_uploadable_leads(campaign_id)
            if uploadable:
                count = upload.upload_leads(campaign_id, uploadable)
                if count > 0:
                    db.mark_uploaded([lead["email"] for lead in uploadable[:count]])
                click.echo(f"Uploaded {count} leads.")
            else:
                click.echo("No verified leads to upload.")

    click.echo("\n=== Done ===")
    stats_cmd.invoke(click.Context(stats_cmd))
