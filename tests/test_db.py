import sqlite3

import pytest

from coldmail.db import (
    get_stats,
    get_unverified_leads,
    get_uploadable_leads,
    init_db,
    insert_leads,
    mark_uploaded,
    update_verified_status,
)
from coldmail.models import Lead


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return path


def make_lead(email="test@example.com", **kwargs):
    defaults = {"source": "generic", "campaign_id": "camp1"}
    defaults.update(kwargs)
    return Lead(email=email, **defaults)


class TestInitDb:
    def test_creates_tables(self, db_path):
        conn = sqlite3.connect(str(db_path))
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
        table_names = [t[0] for t in tables]
        assert "leads" in table_names

    def test_creates_indexes(self, db_path):
        conn = sqlite3.connect(str(db_path))
        indexes = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        conn.close()
        index_names = [i[0] for i in indexes]
        assert "idx_email" in index_names
        assert "idx_verified_status" in index_names
        assert "idx_campaign_id" in index_names


class TestInsertLeads:
    def test_insert_single_lead(self, db_path):
        lead = make_lead()
        inserted, skipped = insert_leads([lead], db_path)
        assert inserted == 1
        assert skipped == 0

    def test_insert_multiple_leads(self, db_path):
        leads = [make_lead(f"user{i}@example.com") for i in range(5)]
        inserted, skipped = insert_leads(leads, db_path)
        assert inserted == 5
        assert skipped == 0

    def test_skip_duplicates(self, db_path):
        lead = make_lead()
        insert_leads([lead], db_path)
        inserted, skipped = insert_leads([lead], db_path)
        assert inserted == 0
        assert skipped == 1

    def test_mixed_new_and_duplicate(self, db_path):
        lead1 = make_lead("a@example.com")
        insert_leads([lead1], db_path)
        lead2 = make_lead("b@example.com")
        inserted, skipped = insert_leads([lead1, lead2], db_path)
        assert inserted == 1
        assert skipped == 1


class TestGetUnverifiedLeads:
    def test_returns_unverified(self, db_path):
        insert_leads([make_lead("a@example.com"), make_lead("b@example.com")], db_path)
        leads = get_unverified_leads(10, db_path=db_path)
        assert len(leads) == 2

    def test_respects_limit(self, db_path):
        insert_leads([make_lead(f"u{i}@example.com") for i in range(10)], db_path)
        leads = get_unverified_leads(3, db_path=db_path)
        assert len(leads) == 3

    def test_filters_by_campaign(self, db_path):
        insert_leads(
            [
                make_lead("a@example.com", campaign_id="c1"),
                make_lead("b@example.com", campaign_id="c2"),
            ],
            db_path,
        )
        leads = get_unverified_leads(10, campaign_id="c1", db_path=db_path)
        assert len(leads) == 1
        assert leads[0]["email"] == "a@example.com"

    def test_excludes_verified(self, db_path):
        insert_leads([make_lead()], db_path)
        update_verified_status("test@example.com", "ok", db_path)
        leads = get_unverified_leads(10, db_path=db_path)
        assert len(leads) == 0


class TestUpdateVerifiedStatus:
    def test_updates_status(self, db_path):
        insert_leads([make_lead()], db_path)
        update_verified_status("test@example.com", "ok", db_path)
        leads = get_unverified_leads(10, db_path=db_path)
        assert len(leads) == 0


class TestGetUploadableLeads:
    def test_returns_verified_not_uploaded(self, db_path):
        insert_leads([make_lead()], db_path)
        update_verified_status("test@example.com", "ok", db_path)
        leads = get_uploadable_leads("camp1", db_path)
        assert len(leads) == 1

    def test_excludes_already_uploaded(self, db_path):
        insert_leads([make_lead()], db_path)
        update_verified_status("test@example.com", "ok", db_path)
        mark_uploaded(["test@example.com"], db_path)
        leads = get_uploadable_leads("camp1", db_path)
        assert len(leads) == 0

    def test_excludes_unverified(self, db_path):
        insert_leads([make_lead()], db_path)
        leads = get_uploadable_leads("camp1", db_path)
        assert len(leads) == 0


class TestMarkUploaded:
    def test_marks_leads(self, db_path):
        insert_leads([make_lead("a@example.com"), make_lead("b@example.com")], db_path)
        mark_uploaded(["a@example.com"], db_path)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT uploaded_to_instantly FROM leads WHERE email = 'a@example.com'"
        ).fetchone()
        conn.close()
        assert row["uploaded_to_instantly"] == 1


class TestGetStats:
    def test_empty_db(self, db_path):
        stats = get_stats(db_path)
        assert stats["total"] == 0
        assert stats["uploaded"] == 0

    def test_with_data(self, db_path):
        insert_leads(
            [
                make_lead("a@example.com", campaign_id="c1"),
                make_lead("b@example.com", campaign_id="c1"),
            ],
            db_path,
        )
        update_verified_status("a@example.com", "ok", db_path)
        stats = get_stats(db_path)
        assert stats["total"] == 2
        assert stats["by_status"]["ok"] == 1
        assert stats["by_status"]["unverified"] == 1
        assert stats["by_campaign"]["c1"] == 2
