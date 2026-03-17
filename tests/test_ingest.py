from pathlib import Path

from coldmail.ingest import parse_csv

FIXTURES = Path(__file__).parent / "fixtures"


class TestParseGenericCsv:
    def test_parses_all_rows(self):
        leads, warnings = parse_csv(FIXTURES / "generic.csv", "generic", "camp1")
        assert len(leads) == 3
        assert len(warnings) == 0

    def test_maps_fields_correctly(self):
        leads, _ = parse_csv(FIXTURES / "generic.csv", "generic", "camp1")
        alice = leads[0]
        assert alice.email == "alice@example.com"
        assert alice.first_name == "Alice"
        assert alice.last_name == "Smith"
        assert alice.company_name == "Acme Corp"
        assert alice.title == "CEO"
        assert alice.company_size == "500"
        assert alice.source == "generic"
        assert alice.campaign_id == "camp1"

    def test_lowercases_email(self):
        leads, _ = parse_csv(FIXTURES / "generic.csv", "generic", "camp1")
        for lead in leads:
            assert lead.email == lead.email.lower()


class TestParseProspecoCsv:
    def test_parses_prospeo_format(self):
        leads, warnings = parse_csv(FIXTURES / "prospeo.csv", "prospeo", "camp1")
        assert len(leads) == 2
        assert leads[0].email == "dana@example.com"
        assert leads[0].company_name == "TechCo"


class TestParseOceanCsv:
    def test_parses_ocean_format(self):
        leads, warnings = parse_csv(FIXTURES / "ocean.csv", "ocean", "camp1")
        assert len(leads) == 2
        assert leads[0].email == "frank@example.com"
        assert leads[0].company_name == "OceanCorp"
        assert leads[0].title == "Engineer"


class TestParseDiscolikeCsv:
    def test_parses_discolike_format(self):
        leads, warnings = parse_csv(FIXTURES / "discolike.csv", "discolike", "camp1")
        assert len(leads) == 2
        assert leads[0].email == "hank@example.com"
        assert leads[0].company_name == "DiscoCo"


class TestBadRows:
    def test_skips_invalid_emails(self):
        leads, warnings = parse_csv(FIXTURES / "bad_rows.csv", "generic", "camp1")
        assert len(leads) == 2
        assert len(warnings) == 2
        emails = [lead.email for lead in leads]
        assert "valid@example.com" in emails
        assert "also-valid@example.com" in emails

    def test_warning_messages(self):
        _, warnings = parse_csv(FIXTURES / "bad_rows.csv", "generic", "camp1")
        assert any("Row 3" in w for w in warnings)
        assert any("Row 4" in w for w in warnings)


class TestCustomMapping:
    def test_custom_mapping_json(self, tmp_path):
        csv_file = tmp_path / "custom.csv"
        csv_file.write_text("E-Mail,Name,Org\njoe@example.com,Joe,JoeCo\n")
        mapping = '{"email": "E-Mail", "first_name": "Name", "company_name": "Org"}'
        leads, _ = parse_csv(csv_file, "generic", "camp1", mapping=mapping)
        assert len(leads) == 1
        assert leads[0].email == "joe@example.com"
        assert leads[0].first_name == "Joe"
        assert leads[0].company_name == "JoeCo"
