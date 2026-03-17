from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Optional

from coldmail.models import Lead

# Predefined column mappings per lead source.
# Keys are our canonical field names, values are the CSV column header.
COLUMN_MAPPINGS: dict[str, dict[str, str]] = {
    "prospeo": {
        "email": "Email",
        "first_name": "First Name",
        "last_name": "Last Name",
        "company_name": "Company Name",
        "title": "Title",
        "company_size": "Company Size",
    },
    "ocean": {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "company_name": "company",
        "title": "job_title",
        "company_size": "company_size",
    },
    "discolike": {
        "email": "Email Address",
        "first_name": "First Name",
        "last_name": "Last Name",
        "company_name": "Company",
        "title": "Job Title",
        "company_size": "Employees",
    },
    "generic": {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "company_name": "company_name",
        "title": "title",
        "company_size": "company_size",
    },
}


def parse_csv(
    file_path: Path,
    source: str,
    campaign_id: str,
    mapping: Optional[str] = None,
) -> tuple[list[Lead], list[str]]:
    """Parse a CSV file into Lead objects. Returns (leads, warnings)."""
    if mapping:
        col_map = json.loads(mapping)
    elif source in COLUMN_MAPPINGS:
        col_map = COLUMN_MAPPINGS[source]
    else:
        col_map = COLUMN_MAPPINGS["generic"]

    leads: list[Lead] = []
    warnings: list[str] = []

    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # row 1 is header
            email_col = col_map.get("email", "email")
            email = row.get(email_col, "").strip().lower()

            if not email or "@" not in email:
                warnings.append(f"Row {i}: skipped — missing or invalid email")
                continue

            lead = Lead(
                email=email,
                first_name=_get(row, col_map, "first_name"),
                last_name=_get(row, col_map, "last_name"),
                company_name=_get(row, col_map, "company_name"),
                title=_get(row, col_map, "title"),
                company_size=_get(row, col_map, "company_size"),
                source=source,
                campaign_id=campaign_id,
            )
            leads.append(lead)

    return leads, warnings


def _get(row: dict, col_map: dict, field: str) -> Optional[str]:
    """Safely get a mapped field from a CSV row."""
    csv_col = col_map.get(field)
    if not csv_col:
        return None
    value = row.get(csv_col, "").strip()
    return value if value else None
