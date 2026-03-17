from unittest.mock import MagicMock, patch

import httpx
import pytest

from coldmail.upload import list_campaigns, upload_leads


class TestListCampaigns:
    @patch("coldmail.upload.httpx.get")
    def test_returns_campaigns(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "items": [{"id": "c1", "name": "Campaign 1"}, {"id": "c2", "name": "Campaign 2"}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        campaigns = list_campaigns()
        assert len(campaigns) == 2
        assert campaigns[0]["name"] == "Campaign 1"

    @patch("coldmail.upload.httpx.get")
    def test_raises_on_error(self, mock_get):
        mock_get.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=MagicMock()
        )
        with pytest.raises(httpx.HTTPStatusError):
            list_campaigns()


class TestUploadLeads:
    @patch("coldmail.upload.httpx.post")
    def test_uploads_single_batch(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        leads = [{"email": f"u{i}@example.com"} for i in range(5)]
        count = upload_leads("camp1", leads)
        assert count == 5
        assert mock_post.call_count == 1

    @patch("coldmail.upload.httpx.post")
    def test_batches_large_uploads(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        leads = [{"email": f"u{i}@example.com"} for i in range(250)]
        count = upload_leads("camp1", leads, batch_size=100)
        assert count == 250
        assert mock_post.call_count == 3  # 100 + 100 + 50

    @patch("coldmail.upload.httpx.post")
    def test_handles_batch_error(self, mock_post):
        mock_resp_ok = MagicMock()
        mock_resp_ok.raise_for_status = MagicMock()

        mock_post.side_effect = [
            mock_resp_ok,
            httpx.HTTPError("500"),
            mock_resp_ok,
        ]

        leads = [{"email": f"u{i}@example.com"} for i in range(250)]
        count = upload_leads("camp1", leads, batch_size=100)
        # First batch succeeds (100), second fails (0), third succeeds (50)
        assert count == 150

    @patch("coldmail.upload.httpx.post")
    def test_sends_correct_payload(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        leads = [{
            "email": "test@example.com", "first_name": "Test",
            "last_name": "User", "company_name": "Co",
        }]
        upload_leads("camp1", leads)

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs["json"]
        assert payload["campaign_id"] == "camp1"
        assert payload["leads"][0]["email"] == "test@example.com"
        assert payload["leads"][0]["first_name"] == "Test"
